import tensorflow as tf
import numpy as np
from tensorflow.keras import backend as K
from tensorflow.keras.layers import Lambda, Input, Dense, concatenate

"""conv1d_tranpose function"""
def conv1d_transpose_wrap(value,
                          filter,
                          output_shape,
                          stride,
                          padding="SAME",
                          data_format="NWC",
                          name=None):
    """Wrap the built-in (contrib) conv1d_transpose function so that output
    has a batch size determined at runtime, rather than being fixed by whatever
    batch size was used during training"""

    dyn_input_shape = tf.shape(value)
    batch_size = dyn_input_shape[0]
    output_shape = tf.stack([batch_size, output_shape[1], output_shape[2]])

    return tf.contrib.nn.conv1d_transpose(
        value,
        filter,
        output_shape,
        stride,
        padding=padding,
        data_format=data_format,
        name=name
    )

# reparameterization trick
# instead of sampling from Q(z|X), sample eps = N(0,I)
# z = z_mean + sqrt(var)*eps
def sampling(args):
    """Reparameterization trick by sampling fr an isotropic unit Gaussian.

    # Arguments
        args (tensor): mean and log of variance of Q(z|X)

    # Returns
        z (tensor): sampled latent vector
    """

    z_mean, z_log_var = args
    batch = K.shape(z_mean)[0]
    dim = K.int_shape(z_mean)[1]
    # by default, random_normal has mean=0 and std=1.0
    epsilon = K.random_normal(shape=(batch, dim))
    return z_mean + K.exp(0.5 * z_log_var) * epsilon
 
def MakeBoundaryLoss(Geometry_tensor, boundary):
    """
    Make the boundary loss using boundary given
    :param Geometry_tensor: 8 element geometry h0 h1 h2 h3 r0 r1 r2 r3
    :param boundary: 4 element numpy array representing [h_low, h_high, r_low, r_high]
    return Boundary_loss: loss that depend on the boundary loss
    """
    tolerance = 1
    print("Geometry_tensor_shape",Geometry_tensor.shape)
    #Make constants
    print(boundary[0] * np.ones([1,4]))
    h_low  = tf.constant((boundary[0] - tolerance) * np.ones([1,4]), name= 'h_low',dtype=tf.float32)
    h_high = tf.constant((boundary[1] + tolerance) * np.ones([1,4]), name= 'h_high',dtype=tf.float32)
    r_low  = tf.constant((boundary[2] - tolerance) * np.ones([1,4]), name= 'r_low',dtype=tf.float32)
    r_high = tf.constant((boundary[3] + tolerance) * np.ones([1,4]), name= 'r_high',dtype=tf.float32)
    
    #Get the 2 separate parts
    h = Geometry_tensor[:,0:4]
    r = Geometry_tensor[:,4:]
    zero = tf.constant(0,dtype=tf.float32,name='zero')
    
    print("shape of h:",h.shape)
    print("shape of r:",r.shape)
    print("shape of h_low:",h_low.shape)
    Boundary_loss = tf.reduce_sum(tf.math.maximum(zero, tf.math.subtract(h, h_high)) + tf.math.maximum(zero, tf.math.subtract(h_low, h) ) +\
                                  tf.math.maximum(zero, tf.math.subtract(r, r_high)) + tf.math.maximum(zero, tf.math.subtract(r_low, r) ))
    return Boundary_loss
#The backward model part
def spectra_encoder(labels,  fc_filters,  reg_scale):
    """
    My customized model function
    :param labels: input spectrum
    :param output_size: dimension of output data
    :return:
    """
    
    ##Building the model
    with tf.name_scope("Spectra_encoder"):
      preConv = tf.expand_dims(labels, axis=2)
      conv = tf.keras.layers.Conv1D(1, 2, strides = 2,padding = 'same',
                                    activation = None, name = 'Conv1d')(preConv)
      backward_fc = tf.squeeze(conv, axis=2)
      for cnt, filters in enumerate(fc_filters):
          backward_fc = tf.layers.dense(inputs=backward_fc, units=filters, activation=tf.nn.leaky_relu, name='spectra_fc{}'.format(cnt),
                               kernel_initializer=tf.random_normal_initializer(stddev=0.02),
                               kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=reg_scale))
      spectra_out = backward_fc
      
    print("spectra_out.shape", spectra_out.shape)
    return spectra_out


def Encoder(geometry, spectra_out, latent_dim, batch_size, reg_scale, encoder_fc_filters):
    XY_pair = concatenate([geometry, spectra_out], name = 'XY_pair')
    encoder_fc = XY_pair
    for cnt, filters in enumerate(encoder_fc_filters):
        encoder_fc = tf.layers.dense(inputs=encoder_fc, units=filters, activation=tf.nn.leaky_relu, name='encoder_fc{}'.format(cnt),
                               kernel_initializer=tf.random_normal_initializer(stddev=0.02),
                               kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=reg_scale))
    z_mean = tf.layers.dense(inputs = encoder_fc, units = latent_dim, activation = tf.nn.leaky_relu,
                                name = 'z_mean',kernel_initializer = tf.random_normal_initializer(stddev=0.02),
                                kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=reg_scale))
    z_log_var = tf.layers.dense(inputs = encoder_fc, units = latent_dim, activation = tf.nn.leaky_relu,
                                name = 'z_log_var',kernel_initializer = tf.random_normal_initializer(stddev=0.02),
                                kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=reg_scale))
    
    return z_mean, z_log_var

def Decoder(z, spectra_out,  batch_size, reg_scale, decoder_fc_filters):
    #First, use the reparameterization trick to push the sampling out as input
    decoder_fc = concatenate([z, spectra_out])
    for cnt, filters in enumerate(decoder_fc_filters):
        decoder_fc = tf.layers.dense(inputs=decoder_fc, units=filters, activation=tf.nn.leaky_relu, name='decoder_fc{}'.format(cnt),
                               kernel_initializer=tf.random_normal_initializer(stddev=0.02),
                               kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=reg_scale))
    decoder_out = decoder_fc
    return decoder_out



def VAE(geometry, spectra, latent_dim,  batch_size, reg_scale, spectra_fc_filters,
        encoder_fc_filters, decoder_fc_filters, boundary):
    spectra_out = spectra_encoder(spectra, spectra_fc_filters, reg_scale)
    z_mean, z_log_var = Encoder(geometry, spectra_out, latent_dim, batch_size, reg_scale, encoder_fc_filters)
    z = Lambda(sampling, output_shape=(latent_dim,), name = 'z')([z_mean, z_log_var])
    decoder_out = Decoder(z, spectra_out, batch_size, reg_scale, decoder_fc_filters)
    Boundary_loss = MakeBoundaryLoss(decoder_out, boundary)
    return z_mean, z_log_var, decoder_out, Boundary_loss

INPUT_SIZE = 2
CLIP = 15
SPECTRA_FC_FILTERS = (100, 500,300,100,30)
ENCODER_FC_FILTERS = (100, 500,300,100,50)
DECODER_FC_FILTERS = (100, 500,300,100,8)
LATENT_DIM = 20
#FORWARD_FC_FILTERS = (100, 500, 1000, 500, 2000, 1000, 500, 165)
#TCONV_FNUMS = (4, 4, 4)
#TCONV_DIMS = (165, 165, 330)
#TCONV_FILTERS = (8, 4, 4)
#N_FILTER = [15]
#N_BRANCH = 2
REG_SCALE = 5e-8
CROSS_VAL = 5
VAL_FOLD = 0
BATCH_SIZE = 2048
SHUFFLE_SIZE = 2000
VERB_STEP = 500
EVAL_STEP = 1000
TRAIN_STEP = 100000
BACKWARD_TRAIN_STEP = 150000
LEARN_RATE = 1e-4
DECAY_STEP = 25000
DECAY_RATE = 0.5
X_RANGE = [i for i in range(2, 10 )]
Y_RANGE = [i for i in range(10 , 2011 )]
# TRAIN_FILE = 'bp2_OutMod.csv'
# VALID_FILE = 'bp2_OutMod.csv'
FORWARDMODEL_CKPT = None#'models/20190814_152255'
STOP_THRESHOLD = 1e-3
FORCE_RUN = True
MODEL_NAME  = '20190823_134730'
DATA_DIR = '../'
GEOBOUNDARY =[30,52,42,52]
NORMALIZE_INPUT = True
DETAIL_TRAIN_LOSS_FORWARD = False
CONV1D_FILTERS = (160, 5)
CONV_CHANNEL_LIST = (4,1)
WRITE_WEIGHT_STEP = 5000



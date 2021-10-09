from sacred import Experiment
from Config import config_ingredient
import Evaluate
import os

ex = Experiment('Mixwaveunet Prediction', ingredients=[config_ingredient])

@ex.config
def cfg():
    model_path = os.path.join("checkpoints", "wet", "wet-1108000") # Load wet pretrained model by default

    input_path = {'hi-hat': '/content/Mix-Wave-U-Net/audio_examples/inputs/hihat.wav',
  'kick': '/content/Mix-Wave-U-Net/audio_examples/inputs/kick.wav',
  'mix': '/content/Mix-Wave-U-Net/audio_examples/inputs/wet_mix.wav',
  'overhead_L': '/content/Mix-Wave-U-Net/audio_examples/inputs/overheadL.wav',
  'overhead_R': '/content/Mix-Wave-U-Net/audio_examples/inputs/overheadR.wav',
  'snare': '/content/Mix-Wave-U-Net/audio_examples/inputs/snare.wav',
  'tom_1': '/content/Mix-Wave-U-Net/audio_examples/inputs/tom1.wav',
  'tom_2': '/content/Mix-Wave-U-Net/audio_examples/inputs/tom2.wav',
  'tom_3': None}

    output_path = '/content/Mix-Wave-U-Net/audio_examples/outputs/wet_mix.wav'
    

@ex.automain
def main(cfg, model_path, input_path, output_path):
    model_config = cfg["model_config"]
    Evaluate.produce_outputs(model_config, model_path, input_path, output_path)

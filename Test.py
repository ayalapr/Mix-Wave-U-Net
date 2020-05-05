import tensorflow as tf
import numpy as np
import os

import Datasets
import Models.UnetAudioSeparator

def test(model_config, partition, model_folder, load_model):
    # Determine input and output shapes
    disc_input_shape = [model_config["batch_size"], model_config["num_frames"], 0]  # Shape of discriminator input
    if model_config["network"] == "unet":
        separator_class = Models.UnetAudioSeparator.UnetAudioSeparator(model_config)
    else:
        raise NotImplementedError

    sep_input_shape, sep_output_shape = separator_class.get_padding(np.array(disc_input_shape))
    separator_func = separator_class.get_output

    # Creating the batch generators
    assert ((sep_input_shape[1] - sep_output_shape[1]) % 2 == 0)
    dataset = Datasets.get_dataset(model_config, sep_input_shape, sep_output_shape, partition=partition)
    iterator = dataset.make_one_shot_iterator()
    batch = iterator.get_next()
    
    batch_input = tf.concat([batch[key] for key in sorted(batch.keys()) if key != 'mix'], 2)

    print("Testing...")

    # BUILD MODELS
    # Separator
    separator_sources = separator_func(batch_input, training=False, reuse=False)  # Sources are output in order [acc, voice] for voice separation, [bass, drums, other, vocals] for multi-instrument separation

    global_step = tf.compat.v1.get_variable('global_step', [], initializer=tf.constant_initializer(0), trainable=False, dtype=tf.int64)

    # Start session and queue input threads
    sess = tf.compat.v1.Session()
    sess.run(tf.compat.v1.global_variables_initializer())
    writer = tf.compat.v1.summary.FileWriter(model_config["log_dir"] + os.path.sep +  model_folder, graph=sess.graph)

    # CHECKPOINTING
    # Load pretrained model to test
    restorer = tf.train.Saver(tf.compat.v1.global_variables(), write_version=tf.compat.v1.train.SaverDef.V2)
    print("Num of variables" + str(len(tf.compat.v1.global_variables())))
    restorer.restore(sess, load_model)
    print('Pre-trained model restored for testing')

    # Start training loop
    _global_step = sess.run(global_step)
    print("Starting!")

    total_loss = 0.0
    batch_num = 1

    # Supervised objective: MSE for raw audio, MAE for magnitude space (Jansson U-Net)
    separator_loss = 0
    real_source = batch['mix']
    sep_source = separator_sources['mix']

    separator_loss += tf.reduce_mean(tf.abs(real_source - sep_source))
        
    while True:
        try:
            curr_loss = sess.run(separator_loss)
            total_loss = total_loss + (1.0 / float(batch_num)) * (curr_loss - total_loss)
            batch_num += 1
        except tf.errors.OutOfRangeError as e:
            break

    summary = tf.compat.v1.summary(value=[tf.compat.v1.summary.Value(tag="test_loss", simple_value=total_loss)])
    writer.add_summary(summary, global_step=_global_step)

    writer.flush()
    writer.close()

    print("Finished testing - Mean MSE: " + str(total_loss))

    # Close session, clear computational graph
    sess.close()
    tf.reset_default_graph()

    return total_loss
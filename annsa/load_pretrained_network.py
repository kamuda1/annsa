import tensorflow as tf
import pickle
import numpy as np
import os
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer

from annsa.model_classes import (cnn1d_model_features,
                                 CNN1D,
                                 CAE,
                                )


def save_features(model_features,
                  filename):
    '''
    Saves model features to a pickled file
    
    inputs:
        model_features : model features class
            The class containing the model features
        filename : str
            The location of the pickled file
    outputs:
        None
    '''
    with open(filename, 'wb+') as f:
        pickle.dump(model_features,f)
    return None


def load_features(filename):
    '''
    Loads model features from a pickled file
    
    inputs:
        filename : str
            The location of the pickled file
    outputs:
        model_features : model features class
            The class containing the model features
    '''

    with open(filename,"rb") as f:
            model_features = pickle.load(f)
    return model_features




def load_pretrained_cae_into_cnn(cae_features_filename,
                        cae_weights_filename,
                        cnn_dense_nodes=[128],
                        learining_rate=1e-4,
                        batch_size=32,
                        output_size=30,
                        activation_function=tf.nn.tanh,
                        l2_regularization_scale=0.0,
                        dropout_probability=0.0):
    '''
    Initialized a CNN with a pretrained CAE for fine-tuning.

    inputs:
        cae_features_filename : str
            Filname location of the pickle file containing the CAE features
        cae_weights_filename : str
            Filname location of the file containing the CAE pretrained weights
        cnn_dense_nodes : list, int (optional)
            List of integers describing the dense part of the CNN
        learining_rate : float (optional)
            Learning rate for the CNN
        batch_size : int (optional)
            Training batch size for the CNN
        output_size : int (optional)
            Output size for the CNN
        activation_function : tensorflow function
            Activation function for the CNN
        l2_regularization_scale : float (optional)
            The dropout probability for the dense layer
        dropout_probability : float (optional)
            The dropout probability for the dense layer
    outputs:
        model_features : model features class
            The class containing the model features
    '''

    cae_features = load_features(cae_features_filename)
    CAE_model = CAE(cae_features)
    CAE_model.load_weights(cae_weights_filename)

    # need to do a forward pass to initialize weights
    dummy_data = np.zeros(1024)
    _ = CAE_model.encoder([dummy_data])

    model_features_CNN = cnn1d_model_features(
        learining_rate=learining_rate,
        trainable=True,
        batch_size=batch_size,
        output_size=output_size,
        output_function=None,
        l2_regularization_scale=l2_regularization_scale,
        dropout_probability=dropout_probability,
        scaler=make_pipeline(FunctionTransformer(np.log1p, validate=True)),
        Pooling=tf.layers.MaxPooling1D,
        cnn_filters=cae_features.cnn_filters_encoder,
        cnn_kernel=cae_features.cnn_kernel_encoder,
        cnn_strides=cae_features.cnn_strides_encoder,
        pool_size=cae_features.pool_size_encoder,
        pool_strides=cae_features.pool_strides_encoder,
        dense_nodes=cnn_dense_nodes,
        activation_function=activation_function,
        )

    CNN_model = CNN1D(model_features_CNN)
    optimizer = tf.train.AdamOptimizer(model_features_CNN.learining_rate)

    # need to do a forward pass to initialize weights
    dummy_data = np.zeros(1024)
    _ = CNN_model.predict_class([dummy_data])

    for i in range(len(cae_features.cnn_filters_encoder)):
        CNN_model.layers[i].set_weights(CAE_model.layers[i].get_weights())

    return CNN_model, model_features_CNN
    
    












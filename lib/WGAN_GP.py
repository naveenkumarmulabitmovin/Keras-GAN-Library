'''
    Improved Training of Wasserstein GANs
    Ref:
        https://arxiv.org/abs/1704.00028
'''

import keras.backend as K
from keras.models import Sequential
from keras.layers import Conv2D,GlobalAveragePooling2D,LeakyReLU,Conv2DTranspose
from keras.optimizers import Adam
from keras.layers import Input

def build_generator(input_shape):
    model = Sequential()

    model.add(Conv2DTranspose(512,(3,3),strides=(2,2),padding="same",input_shape=input_shape))
    model.add(LeakyReLU(0.2))

    model.add(Conv2DTranspose(256,(3,3),strides=(2,2),padding="same"))
    model.add(LeakyReLU(0.2))

    model.add(Conv2DTranspose(128,(3,3),strides=(2,2),padding="same"))
    model.add(LeakyReLU(0.2))

    model.add(Conv2DTranspose(64,(3,3),strides=(2,2),padding="same"))
    model.add(LeakyReLU(0.2))

    model.add(Conv2D(3,(3,3),padding="same",activation="tanh"))
    return model


def build_discriminator(input_shape):
    model = Sequential()

    model.add(Conv2D(64,(3,3),strides=(2,2),padding="same",input_shape=input_shape))
    model.add(LeakyReLU(0.2))

    model.add(Conv2D(128,(3,3),strides=(2,2),padding="same"))
    model.add(LeakyReLU(0.2))

    model.add(Conv2D(256,(3,3),strides=(2,2),padding="same"))
    model.add(LeakyReLU(0.2))

    model.add(Conv2D(512,(3,3),strides=(2,2),padding="same"))
    model.add(LeakyReLU(0.2))

    model.add(Conv2D(1,(3,3),padding="same"))
    model.add(GlobalAveragePooling2D())

    return model

def get_training_function(batch_size,noise_size,image_size,generator,discriminator):

    real_image = Input(image_size)
    noise = K.random_normal((batch_size,) + noise_size,0.0,1.0,"float32")
    fake_image = generator(noise)

    LAMBA = 10
    alpha = K.random_uniform(minval=0.0, maxval=1.0, shape=(batch_size, 1, 1, 1))
    interpolates = (1 - alpha) * real_image + alpha * fake_image
    grad = K.gradients(discriminator(interpolates), [interpolates])[0]
    norm_grad = K.sqrt(K.sum(K.square(grad), axis=[1, 2, 3]) + K.epsilon())
    grad_penalty = K.mean(K.square(norm_grad - 1))

    pred_real = discriminator(real_image)
    pred_fake = discriminator(fake_image)

    d_loss = K.mean(pred_fake) - K.mean(pred_real) + LAMBA * grad_penalty
    g_loss = -K.mean(pred_fake)

    d_training_updates = Adam(lr=0.0001, beta_1=0.0, beta_2=0.9).get_updates(d_loss, discriminator.trainable_weights)
    d_train = K.function([real_image, K.learning_phase()], [d_loss], d_training_updates)

    g_training_updates = Adam(lr=0.0001, beta_1=0.0, beta_2=0.9).get_updates(g_loss, generator.trainable_weights)
    g_train = K.function([K.learning_phase()], [g_loss], g_training_updates)

    return d_train,g_train
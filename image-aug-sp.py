import numpy as np
import imgaug as ia
import imgaug.augmenters as iaa
import cv2 as cv
from imgaug import parameters as iap



filePath = input("plz enter img path :")
dirPath = input("plz enter dir path :")

augNum = 1

while(augNum % 8 != 0):
    augNum = int(input("plz enter augNum path (? num % 8 == 0):"))

dataformat = input("plz enter output format :")

images = np.array(
    [cv.imread(filePath , 1) for _ in range(int(augNum / 8))],
    dtype=np.uint8
)



ia.seed(1)

def makeModel():

    seq1 = iaa.Sequential([
        iaa.Fliplr(0.5), # horizontal flips
        iaa.Crop(percent=(0, 0.1)), # random crops
        # Small gaussian blur with random sigma between 0 and 0.5.
        # But we only blur about 50% of all images.
        iaa.Sometimes(
            0.5,
            iaa.GaussianBlur(sigma=(0, 0.5))
        ),
        # Strengthen or weaken the contrast in each image.
        iaa.LinearContrast((0.75, 1.5)),
        # Add gaussian noise.
        # For 50% of all images, we sample the noise once per pixel.
        # For the other 50% of all images, we sample the noise per pixel AND
        # channel. This can change the color (not only brightness) of the
        # pixels.
        iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.05*255), per_channel=0.5),
        # Make some images brighter and some darker.
        # In 20% of all cases, we sample the multiplier once per channel,
        # which can end up changing the color of the images.
        iaa.Multiply((0.8, 1.2), per_channel=0.2),
        # Apply affine transformations to each image.
        # Scale/zoom them, translate/move them, rotate them and shear them.
        iaa.Affine(
            scale={"x": (0.8, 1.2), "y": (0.8, 1.2)},
            translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
            rotate=(-25, 25),
            shear=(-8, 8)
        )
    ], random_order=True) # apply augmenters in random order

    sometimes = lambda aug: iaa.Sometimes(0.5, aug)

    # Define our sequence of augmentation steps that will be applied to every image.
    seq2 = iaa.Sequential(
        [
            #
            # Apply the following augmenters to most images.
            #
            iaa.Fliplr(0.5), # horizontally flip 50% of all images
            iaa.Flipud(0.2), # vertically flip 20% of all images

            # crop some of the images by 0-10% of their height/width
            sometimes(iaa.Crop(percent=(0, 0.1))),

            # Apply affine transformations to some of the images
            # - scale to 80-120% of image height/width (each axis independently)
            # - translate by -20 to +20 relative to height/width (per axis)
            # - rotate by -45 to +45 degrees
            # - shear by -16 to +16 degrees
            # - order: use nearest neighbour or bilinear interpolation (fast)
            # - mode: use any available mode to fill newly created pixels
            #         see API or scikit-image for which modes are available
            # - cval: if the mode is constant, then use a random brightness
            #         for the newly created pixels (e.g. sometimes black,
            #         sometimes white)
            sometimes(iaa.Affine(
                scale={"x": (0.8, 1.2), "y": (0.8, 1.2)},
                translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
                rotate=(-45, 45),
                shear=(-16, 16),
                order=[0, 1],
                cval=(0, 255),
                mode=ia.ALL
            )),

            #
            # Execute 0 to 5 of the following (less important) augmenters per
            # image. Don't execute all of them, as that would often be way too
            # strong.
            #
            iaa.SomeOf((0, 5),
                [
                    # Convert some images into their superpixel representation,
                    # sample between 20 and 200 superpixels per image, but do
                    # not replace all superpixels with their average, only
                    # some of them (p_replace).
                    sometimes(
                        iaa.Superpixels(
                            p_replace=(0, 1.0),
                            n_segments=(20, 200)
                        )
                    ),

                    # Blur each image with varying strength using
                    # gaussian blur (sigma between 0 and 3.0),
                    # average/uniform blur (kernel size between 2x2 and 7x7)
                    # median blur (kernel size between 3x3 and 11x11).
                    iaa.OneOf([
                        iaa.GaussianBlur((0, 3.0)),
                        iaa.AverageBlur(k=(2, 7)),
                        iaa.MedianBlur(k=(3, 11)),
                    ]),

                    # Sharpen each image, overlay the result with the original
                    # image using an alpha between 0 (no sharpening) and 1
                    # (full sharpening effect).
                    iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),

                    # Same as sharpen, but for an embossing effect.
                    iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0)),

                    # Search in some images either for all edges or for
                    # directed edges. These edges are then marked in a black
                    # and white image and overlayed with the original image
                    # using an alpha of 0 to 0.7.
                    sometimes(iaa.OneOf([
                        iaa.EdgeDetect(alpha=(0, 0.7)),
                        iaa.DirectedEdgeDetect(
                            alpha=(0, 0.7), direction=(0.0, 1.0)
                        ),
                    ])),

                    # Add gaussian noise to some images.
                    # In 50% of these cases, the noise is randomly sampled per
                    # channel and pixel.
                    # In the other 50% of all cases it is sampled once per
                    # pixel (i.e. brightness change).
                    iaa.AdditiveGaussianNoise(
                        loc=0, scale=(0.0, 0.05*255), per_channel=0.5
                    ),

                    # Either drop randomly 1 to 10% of all pixels (i.e. set
                    # them to black) or drop them on an image with 2-5% percent
                    # of the original size, leading to large dropped
                    # rectangles.
                    iaa.OneOf([
                        iaa.Dropout((0.01, 0.1), per_channel=0.5),
                        iaa.CoarseDropout(
                            (0.03, 0.15), size_percent=(0.02, 0.05),
                            per_channel=0.2
                        ),
                    ]),

                    # Invert each image's channel with 5% probability.
                    # This sets each pixel value v to 255-v.
                    iaa.Invert(0.05, per_channel=True), # invert color channels

                    # Add a value of -10 to 10 to each pixel.
                    iaa.Add((-10, 10), per_channel=0.5),

                    # Change brightness of images (50-150% of original value).
                    iaa.Multiply((0.5, 1.5), per_channel=0.5),

                    # Improve or worsen the contrast of images.
                    iaa.LinearContrast((0.5, 2.0), per_channel=0.5),

                    # Convert each image to grayscale and then overlay the
                    # result with the original with random alpha. I.e. remove
                    # colors with varying strengths.
                    iaa.Grayscale(alpha=(0.0, 1.0)),

                    # In some images move pixels locally around (with random
                    # strengths).
                    sometimes(
                        iaa.ElasticTransformation(alpha=(0.5, 3.5), sigma=0.25)
                    ),

                    # In some images distort local areas with varying strength.
                    sometimes(iaa.PiecewiseAffine(scale=(0.01, 0.05)))
                ],
                # do all of the above augmentations in random order
                random_order=True
            )
        ],
        # do all of the above augmentations in random order
        random_order=True
    )

    seq3 = iaa.Sequential([
        iaa.GaussianBlur(
            sigma=iap.Uniform(0.0, 1.0)
        ),
        iaa.contrast.LinearContrast(
            iap.Choice(
                [1.0, 1.5, 3.0],
                p=[0.5, 0.3, 0.2]
            )
        ),
        iaa.Affine(
            rotate=iap.Normal(0.0, 30),
            translate_px=iap.RandomSign(iap.Poisson(3))
        ),
        iaa.AddElementwise(
            iap.Discretize(
                (iap.Beta(0.5, 0.5) * 2 - 1.0) * 64
            )
        ),
        iaa.Multiply(
            iap.Positive(iap.Normal(0.0, 0.1)) + 1.0
        )
    ])

    seqAddWeather = iaa.Sequential([
    sometimes(
        iaa.Clouds()
    ),
    sometimes(
        iaa.Fog()
    ),
    sometimes(
        iaa.Snowflakes(flake_size=(0.2, 0.7), speed=(0.007, 0.03))
    ),
    sometimes(
        iaa.Rain()
    )
])

    seq4 = iaa.Sequential([
        sometimes(iaa.PiecewiseAffine(scale=(0.01, 0.05))),
        sometimes(iaa.Affine(scale={"x": (0.5, 1.5), "y": (0.5, 1.5)})),
        sometimes(iaa.Canny()),
        sometimes(iaa.Cartoon()),
        iaa.Fliplr(0.5)
    ])

    seq5 = iaa.RandAugment(n=0, m=9)

    seq6 = iaa.Sequential([
        sometimes(iaa.Cartoon()),
        sometimes(iaa.Cutout(nb_iterations=(1, 2), size=0.2, squared=False , cval=(0, 255))),
        sometimes(iaa.MeanShiftBlur()),
        sometimes(iaa.AverageBlur(k=((5, 11), (1, 3))))
    ])

    seq7 = iaa.Sequential([
        sometimes(iaa.GaussianBlur(sigma=(0.0, 3.0))),
        sometimes(iaa.BlendAlphaFrequencyNoise(
                    foreground=iaa.EdgeDetect(1.0),
                    per_channel=True
                    )),
        sometimes(iaa.BlendAlphaFrequencyNoise(
                    foreground=iaa.Multiply(iap.Choice([0.5, 1.5]), per_channel=True)
                    )),
        sometimes(iaa.BlendAlphaSimplexNoise(
                    foreground=iaa.EdgeDetect(1.0),
                    per_channel=True
                    )),
        sometimes(iaa.BlendAlphaSimplexNoise(
                    foreground=iaa.Multiply(iap.Choice([0.5, 1.5]), per_channel=True)
                    ))
    ])



    return seq1 , seq2 , seq3 , seqAddWeather , seq4 , seq5 , seq6 , seq7





seq1 , seq2 , seq3 , seqAddWeather , seq4 , seq5 , seq6 , seq7 = makeModel()




images_aug1 = seq1(images=images)
images_aug2 = seq2(images=images)
images_aug3 = seq3(images=images)
images_augAddWeather = seqAddWeather(images=images)
images_aug4 = seq4(images=images)
images_aug5 = seq5(images=images)
images_aug6 = seq6(images=images)
images_aug7 = seq7(images=images)



imagesOutPut = np.concatenate((images_aug1 , images_aug2 , images_aug3 , images_aug4 , images_aug5 , images_aug6 , images_aug7 , images_augAddWeather) )

for i in range(0 , augNum):

    cv.imwrite(dirPath+"/"+str(i + 1) +" img" +"."+dataformat ,imagesOutPut[i])



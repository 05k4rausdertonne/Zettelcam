from PIL import Image, ImageFilter, ImageOps
import numpy as np
from scipy import ndimage
from math import floor

def bw_pil_image_from_array(arr):
    to_display = Image.new("L", arr.shape, 0)
    to_display.putdata(arr.flatten())
    return to_display

def boxfilter(img, radius):
    height, width = img.shape
    out_image = np.zeros(img.shape)
    for i in range(height):
        for j in range(width):
            x1 = max(min(i-radius, height), 1)
            x2 = max(min(i+radius, height), 1)
            y1 = max(min(j-radius, width ), 1)
            y2 = max(min(j+radius, width ), 1)
            out_image[i, j] = np.sum(img[x1:x2, y1:y2])
    return out_image

def edgeaware(img, radius):
    (height, width) = img.shape
    L = img.max()-img.min()
    eps = (0.001*L)**2
    mean_I = ndimage.uniform_filter(img, size=radius, mode='mirror') # calc_mean(image, radius, N)
    corr_I = ndimage.uniform_filter(img*img, size=radius, mode='mirror') # calc_mean(img .* img, r, N)
    var_I = corr_I - mean_I * mean_I
    gamma = (var_I + eps) * sum(1 / (var_I + eps)) / (height*width)
    return gamma

# https://github.com/wjymonica/WGIF-and-GIF
def wgif(img, guide, radius, llambda):
    gamma = edgeaware(img, 1)
    (height, width) = img.shape
    #step 1:
    mean_img = ndimage.uniform_filter(img, size=radius, mode='mirror') #calc_mean(img, r, N)
    mean_guide = ndimage.uniform_filter(guide, size=radius, mode='mirror') #calc_mean(guide, r, N)
    corr_img = ndimage.uniform_filter(img*img, size=radius, mode='mirror') #calc_mean(img .*img, r, N)
    corr_Ip = ndimage.uniform_filter(img*guide, size=radius, mode='mirror') #calc_mean(img .*guide, r, N)

    #step 2:
    var_I = corr_img - mean_img * mean_img
    cov_Ip = corr_Ip - mean_img * mean_guide

    #step 3:
    a = cov_Ip / (var_I + llambda / gamma)
    b = mean_guide - a * mean_img

    #step 4:
    mean_a = ndimage.uniform_filter(a, size=radius, mode='mirror') #calc_mean(a, r, N)
    mean_b = ndimage.uniform_filter(b, size=radius, mode='mirror') #calc_mean(b, r, N)

    q = mean_a * img + mean_b
    return q
    
# https://link.springer.com/article/10.1007/s41095-021-0232-x
# 1) Load original RGB color image S(x, y), convert to HSI color model, select intensity image SI (x, y).
def image_enhancement(image):
    [width, height] = image.size;
    S_I = np.reshape(image.convert('L').getdata(), (width, height))
# 2) Enhance intensity image
	# Compute and process illumination component
	# 1. Use WGIF to estimate illumination component of intensity: SILi(x, y) = aiSIi(x, y) + bi
    S_IL_PRE = wgif(S_I, S_I, 3, 0.001)
    S_IL_PRE = np.clip(S_IL_PRE,0.1,255)
    S_IL = S_IL_PRE / 255
    #display(bw_pil_image_from_array(S_IL*255))
	#  Adaptive brightness equalization
	#  	2. Correct the illumination component using adaptive gamma function: SILG(x, y) = SIL(x, y))f(x,y)
    a = 1 - (np.mean(S_IL))
    gamma = (S_IL + a)/(1+a)
    S_ILG = np.abs(S_IL) ** gamma
    
	#  	3. Perform global linear stretching: SILGf (x, y) = SILG(x,y)-min(SILG(x,y)) / max(SILG(x,y))-min(SILG(x,y))
    S_ILGf = (S_ILG - np.min(S_ILG)) / (np.max(S_ILG) - np.min(S_ILG))
	# Compute and process reflection component image
	# 	4. Compute the reflection component: SIR(x, y) = SI (x, y)/SIL(x, y)
    S_IR = S_I / S_IL_PRE
	# 	5. Denoise the reflection component using WGIF: SIRHi(x, y) = aiSIR(x, y) + bi
    S_IRH = wgif(S_IR*255, S_IR*255, 3, 0.001) / 255
    
    
# 3) Image fusion
    # Fuse the processed illumination component and reflection component
    # 1. Compute the enhanced intensity image: SIE(x, y) = SILGf (x, y)SIRH(x, y)
    S_IE = S_ILGf * S_IRH
    # 2.Improve the brightness of the fused image using the S-hyperbolic tangent function:
    b = np.mean(S_IE)
    S_IEf = 1 / (1 + np.exp(-8* (S_IE-b)))
    #display(bw_pil_image_from_array(S_IEf*255))
    return bw_pil_image_from_array(S_IEf*255)
    #print('CAT RESTORED:')
    #print(S_IE*255)
# 4) Color restoration
    # 	1. Calculate the brightness gain coefficient: a(x, y) = SIEf (x, y)/SI (x, y)
    # 	2. Convert the enhanced HSI image to RGB by linear color restoration R1(x, y) = a(x, y)R0(x, y) G1(x, y) = a(x, y)G0(x, y) B1(x, y) = a(x, y)B0(x, y)
    #pass
    
def custom_bw_enhancement(photo):
  bw = photo.filter(ImageFilter.EDGE_ENHANCE).convert('L')
  enhanced = image_enhancement(bw)
  return ImageOps.colorize(\
    ImageOps.autocontrast(enhanced),\
    (0,0,0), (255,255,255), blackpoint=0, whitepoint=255, midpoint=80)
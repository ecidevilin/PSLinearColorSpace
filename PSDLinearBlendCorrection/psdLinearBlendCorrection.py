import numpy
import pytoshop
from pytoshop.user import nested_layers
def GetVisibleLayers(all, vt):
    for layer in all:
        if layer.visible:
            if isinstance(layer,nested_layers.Group):
                GetVisibleLayers(layer.layers, vt)
            else:
                vt.append(layer)

def Gamma2Linear(v):
    r = v / 12.92
    if v > 0.04045:
        r = pow((v + 0.055) / 1.055, 2.4)
    return r
    # return round(r * 255) / 255

def Linear2Gamma(v):
    r = 12.92 * v
    if v > 0.0031308:
        r = 1.055 * pow(v, 1/2.4) - 0.055
    return r
    # return round(r * 255) / 255

def EightBitsCorrection(v):
    return round(v * 255) / 255

with open('1.psd', 'rb') as fd:
    psd = pytoshop.read(fd)
    width = psd.width
    height = psd.height
    layers = nested_layers.psd_to_nested_layers(psd)
    vt = []
    GetVisibleLayers(layers, vt)
    print(vt)
    print(width)
    print(height)
    rbuffer = numpy.zeros((width,height),numpy.uint8)
    gbuffer = numpy.zeros((width,height),numpy.uint8)
    bbuffer = numpy.zeros((width,height),numpy.uint8)
    for i in range(len(vt), 0, -1):
        l = vt[i - 1]
        left = l.left
        top = l.top
        print(top)
        print(left)
        if l.channels.get(-1, None) != None:
            achannel = l.channels[-1].image
            acchannel = numpy.zeros(achannel.shape, numpy.uint8)
            rchannel = l.channels[0].image
            rcchannel = numpy.zeros(rchannel.shape, numpy.uint8)
            gchannel = l.channels[1].image
            gcchannel = numpy.zeros(gchannel.shape, numpy.uint8)
            bchannel = l.channels[2].image
            bcchannel = numpy.zeros(bchannel.shape, numpy.uint8)
            [row, col] = rchannel.shape
            for x in range(row):
                for y in range(col):
                    srcR = rchannel[x][y] / 255
                    srcG = gchannel[x][y] / 255
                    srcB = bchannel[x][y] / 255
                    alpha = achannel[x][y] / 255
                    dstR = rbuffer[x + left][y + top] / 255
                    dstG = gbuffer[x + left][y + top] / 255
                    dstB = bbuffer[x + left][y + top] / 255

                    crrR = srcR
                    crrG = srcG
                    crrB = srcB
                    crrA = alpha
                    errR = (alpha * srcR + (1 - alpha) * dstR)
                    errG = (alpha * srcG + (1 - alpha) * dstG)
                    errB = (alpha * srcB + (1 - alpha) * dstB)


                    if (alpha > 0):
                        crrR = (Gamma2Linear(errR) - (1 - alpha) * Gamma2Linear(dstR)) / alpha
                        crrG = (Gamma2Linear(errG) - (1 - alpha) * Gamma2Linear(dstG)) / alpha
                        crrB = (Gamma2Linear(errB) - (1 - alpha) * Gamma2Linear(dstB)) / alpha

                    if (crrR > 1 and crrR >= crrG and crrR >= crrB) or (crrR < 0 and crrR <= crrG and crrR <= crrB):
                        crrA = (Gamma2Linear(errR) - Gamma2Linear(dstR)) / (Gamma2Linear(srcR) - Gamma2Linear(dstR))
                    elif (crrG > 1 and crrG >= crrR and crrG >= crrB) or (crrG < 0 and crrG <= crrR and crrG <= crrB):
                        crrA = (Gamma2Linear(errG) - Gamma2Linear(dstG)) / (Gamma2Linear(srcG) - Gamma2Linear(dstG))
                    elif (crrB > 1 and crrB >= crrR and crrB >= crrG) or (crrB < 0 and crrB <= crrR and crrB <= crrG):
                        crrA = (Gamma2Linear(errB) - Gamma2Linear(dstB)) / (Gamma2Linear(srcB) - Gamma2Linear(dstB))
                    crrA = EightBitsCorrection(crrA)
                    if (crrA > 0):
                        crrR = (Gamma2Linear(errR) - (1 - crrA) * Gamma2Linear(dstR)) / crrA
                        crrG = (Gamma2Linear(errG) - (1 - crrA) * Gamma2Linear(dstG)) / crrA
                        crrB = (Gamma2Linear(errB) - (1 - crrA) * Gamma2Linear(dstB)) / crrA

                    assert (round(crrR * 255) <= 255 or round(crrR * 255) >= 0)
                    assert (round(crrG * 255) <= 255 or round(crrG * 255) >= 0)
                    assert (round(crrB * 255) <= 255 or round(crrB * 255) >= 0)

                    if crrR < 1 / 256:
                        crrR = 0
                    if crrG < 1 / 256:
                        crrG = 0
                    if crrB < 1 / 256:
                        crrB = 0
                    crrR = Linear2Gamma(crrR)
                    crrG = Linear2Gamma(crrG)
                    crrB = Linear2Gamma(crrB)
                    rbuffer[x + left][y + top] = round(errR * 255)
                    gbuffer[x + left][y + top] = round(errG * 255)
                    bbuffer[x + left][y + top] = round(errB * 255)
                    rcchannel[x][y] = round(crrR * 255)
                    gcchannel[x][y] = round(crrG * 255)
                    bcchannel[x][y] = round(crrB * 255)
                    acchannel[x][y] = round(crrA * 255)
                    # if (srcr > srcg and srcr > srcb):
                    #     dsterr = (alpha * srcr + (1 - alpha) * dstr)
                    #     if (srcr != dstr):
                    #         alphacor = (pow(dsterr, 2.2) - pow(dstr, 2.2)) / (pow(srcr, 2.2) - pow(dstr, 2.2))
                    # elif (srcg > srcr and srcg > srcb):
                    #     dsterr = (alpha * srcg + (1 - alpha) * dstg)
                    #     if (srcg != dstg):
                    #         alphacor = (pow(dsterr, 2.2) - pow(dstg, 2.2)) / (pow(srcg, 2.2) - pow(dstg, 2.2))
                    # else:
                    #     dsterr = (alpha * srcb + (1 - alpha) * dstb)
                    #     if (srcb != dstb):
                    #         alphacor = (pow(dsterr, 2.2) - pow(dstb, 2.2)) / (pow(srcb, 2.2) - pow(dstb, 2.2))
                    #
                    # dsterr = (alpha * srcr + (1 - alpha) * dstr)
                    # rbuffer[x + left][y + top] = round(dsterr * 255)
                    # dsterr = (alpha * srcg + (1 - alpha) * dstg)
                    # gbuffer[x + left][y + top] = round(dsterr * 255)
                    # dsterr = (alpha * srcb + (1 - alpha) * dstb)
                    # bbuffer[x + left][y + top] = round(dsterr * 255)
                    # acchannel[x][y] = round(alphacor * 255)
            l.channels[-1].image = acchannel
            l.channels[0].image = rcchannel
            l.channels[1].image = gcchannel
            l.channels[2].image = bcchannel
        else:
            rchannel = l.channels[0].image
            gchannel = l.channels[1].image
            bchannel = l.channels[2].image
            [row, col] = rchannel.shape
            for x in range(row):
                for y in range(col):
                    rbuffer[x + left][y + top] = rchannel[x][y]
                    gbuffer[x + left][y + top] = gchannel[x][y]
                    bbuffer[x + left][y + top] = bchannel[x][y]
        print(l.channels)



    # vt[len(vt) - 1].channels[0].image = rbuffer
    # vt[len(vt) - 1].channels[1].image = rbuffer
    # vt[len(vt) - 1].channels[2].image = rbuffer
    psd = nested_layers.nested_layers_to_psd(layers, psd.color_mode)
    with open('2.psd', 'wb') as fd:
        psd.write(fd)
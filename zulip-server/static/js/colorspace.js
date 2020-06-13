// Convert an sRGB value in [0, 255] to a linear intensity
// value in [0, 1].
//
// https://en.wikipedia.org/wiki/SRGB#The_reverse_transformation
exports.sRGB_to_linear = function (v) {
    v = v / 255.0;
    if (v <= 0.04045) {
        return v / 12.92;
    }
    return Math.pow((v + 0.055) / 1.055, 2.4);
};

// Compute luminance (CIE Y stimulus) from linear intensity
// of sRGB / Rec. 709 primaries.
exports.rgb_luminance = function (channel) {
    return 0.2126 * channel[0] + 0.7152 * channel[1] + 0.0722 * channel[2];
};

// Convert luminance (photometric, CIE Y)
// to lightness (perceptual, CIE L*)
//
// https://en.wikipedia.org/wiki/Lab_color_space#Forward_transformation
exports.luminance_to_lightness = function (luminance) {
    let v;
    if (luminance <= 216 / 24389) {
        v = 841 / 108 * luminance + 4 / 29;
    } else {
        v = Math.pow(luminance, 1 / 3);
    }

    return 116 * v - 16;
};

exports.getDecimalColor = function (hexcolor) {
    return {r: parseInt(hexcolor.substr(1, 2), 16),
            g: parseInt(hexcolor.substr(3, 2), 16),
            b: parseInt(hexcolor.substr(5, 2), 16)};
};

exports.getLighterColor = function (rgb, lightness) {
    return {r: Math.round(lightness * 255 + (1 - lightness) * rgb.r),
            g: Math.round(lightness * 255 + (1 - lightness) * rgb.g),
            b: Math.round(lightness * 255 + (1 - lightness) * rgb.b)};
};

exports.getHexColor = function (rgb) {
    return "#" + parseInt(rgb.r, 10).toString(16) +
                 parseInt(rgb.g, 10).toString(16) +
                 parseInt(rgb.b, 10).toString(16);
};

window.colorspace = exports;

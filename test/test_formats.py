from io import BytesIO
from tempfile import TemporaryFile
from unittest.mock import patch

import pytest
from PIL import Image

from imaginex_lambda.handler import handler, S3_BUCKET_NAME, download_and_optimize


def test_handler_success():
    """
    This test will mock the result of the 'download_and_optimize' function
    to return a fixed value. This way we can check if the handler single responsibility
    (to parse the context and generate a formatted response) is working correctly.

    Specific image processing tests should call 'download_and_optimize' directly,
    so it is easier to check for exceptions and edge cases.
    """

    context = {'queryStringParameters': {'url': 'abc.png', 'q': '50', 'w': '100'}}
    fake_optimization_return = (b'abcdef', 'application/someimage', 0.3)

    with patch('imaginex_lambda.handler.download_and_optimize') as p:
        p.return_value = fake_optimization_return
        r = handler(context, None)

    assert r['statusCode'] == 200
    assert r['isBase64Encoded'] is True
    assert r['headers']['Content-Type'] == 'application/someimage'
    assert r['headers']['X-Optimization-Ratio'] == '0.3000'


@pytest.mark.parametrize('expected_ratio,expected_type,q,w,url', [
    (0.0037, 'image/png', 80, 100, "example.png"),
    (0.0109, 'image/jpeg', 40, 250, "https://s3.eu-central-1.amazonaws.com/fllite-dev-main/"
                                    "business_case_custom_images/sun_valley_2_5f84953fef8c6_63a2668275433.jfif"),
    (0.1770, 'image/jpeg', 80, 100, "http://site.meishij.net/r/58/25/3568808/a3568808_142682562777944.jpg"),
    (0.6733, 'image/jpeg', 80, 100, "https://www.gravatar.com/avatar/617bdc1719f77448a4f96eb92e1ac02b?s=80&d=mp"),
])
def test_process_success(expected_ratio, expected_type, q, w, url):
    if not url.startswith('http') and S3_BUCKET_NAME is None:
        pytest.skip('specify a value for S3_BUCKET_NAME to run S3 tests')

    image_data, content_type, ratio = download_and_optimize(url=url, quality=q, width=w)
    assert isinstance(image_data, bytes)
    assert content_type == expected_type
    assert round(ratio, 4) == expected_ratio


@pytest.mark.parametrize('expected_ratio,expected_type,q,w,url', [
    (0.0037, 'image/png', 80, 100, "example.png"),
    (0.0109, 'image/jpeg', 40, 250, "https://s3.eu-central-1.amazonaws.com/fllite-dev-main/"
                                    "business_case_custom_images/sun_valley_2_5f84953fef8c6_63a2668275433.jfif"),
    (0.1770, 'image/jpeg', 80, 100, "http://site.meishij.net/r/58/25/3568808/a3568808_142682562777944.jpg"),
    (0.6733, 'image/jpeg', 80, 100, "https://www.gravatar.com/avatar/617bdc1719f77448a4f96eb92e1ac02b?s=80&d=mp"),
])
def test_process_success(expected_ratio, expected_type, q, w, url):
    if not url.startswith('http') and S3_BUCKET_NAME is None:
        pytest.skip('specify a value for S3_BUCKET_NAME to run S3 tests')

    image_data, content_type, ratio = download_and_optimize(url=url, quality=q, width=w)
    assert isinstance(image_data, bytes)
    assert content_type == expected_type
    assert round(ratio, 4) == expected_ratio


import pytest
from unittest.mock import MagicMock


@pytest.mark.parametrize('img_type,expected_type', [
    ('PNG', 'image/png'),
    ('JPEG', 'image/jpeg'),
    # ('PPM', 'image/ppm'),
    ('GIF', 'image/gif'),
    ('TIFF', 'image/tiff'),
    ('BMP', 'image/bmp'),
])
def test_download_and_optimize_with_valid_url(img_type, expected_type):
    # arrange
    original_w, original_h, new_q, new_w = 300, 300, 80, 200

    sample_url = "https://example.com"
    img = Image.new('RGB', (original_w, original_h), color=(255, 0, 0))
    tmp_img = TemporaryFile()
    img.save(tmp_img, format=img_type)
    download_image_mock = MagicMock(return_value=(tmp_img, {}))

    # act
    with patch('imaginex_lambda.handler.download_image', download_image_mock):
        opt_img_bytes, content_type, ratio = download_and_optimize(sample_url, new_q, new_w)
    tmp_img.close()

    # assert
    opt_img = Image.open(BytesIO(opt_img_bytes))
    assert content_type == expected_type
    assert opt_img.width == new_w

# FORMATS = ['PNG', 'JPEG', 'PPM', 'GIF', 'TIFF', 'BMP']
#
# im_jpeg = Image.new('RGB', (100, 100), color=(255, 0, 0))
# im_jpeg.save('test_image.jpg', 'JPEG')
#
# # Create a 100x100 solid green PNG image
# im_png = Image.new('RGB', (100, 100), color=(0, 255, 0))
# im_png.save('test_image.png', 'PNG')
#
# # Create a 100x100 solid blue BMP image
# im_bmp = Image.new('RGB', (100, 100), color=(0, 0, 255))
# im_bmp.save('test_image.bmp', 'BMP')

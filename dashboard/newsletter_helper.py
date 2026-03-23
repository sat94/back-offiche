import io
import json
import uuid
import base64
import urllib.request
import urllib.parse
from PIL import Image
import boto3
from decouple import config

DEEPINFRA_URL = 'https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-schnell'


def generate_image(prompt, width=768, height=512):
    api_key = config('DEEPINFRA_API_KEY')
    payload = json.dumps({
        'prompt': prompt,
        'width': width,
        'height': height,
        'num_inference_steps': 4,
    }).encode()

    req = urllib.request.Request(DEEPINFRA_URL, data=payload, headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    })
    resp = urllib.request.urlopen(req, timeout=60)
    body = json.loads(resp.read())

    img_data = body.get('images', [None])[0]
    if not img_data:
        raise ValueError('No image returned')

    if img_data.startswith('data:'):
        img_data = img_data.split(',', 1)[1]

    return base64.b64decode(img_data)


def compress_image(image_bytes, max_width=800, quality=75):
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality, optimize=True)
    return buf.getvalue()


def upload_to_s3(image_bytes, filename=None):
    if not filename:
        filename = f'newsletter/{uuid.uuid4().hex}.jpg'

    s3 = boto3.client(
        's3',
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
        region_name=config('AWS_REGION'),
    )
    bucket = config('AWS_S3_BUCKET_NAME')

    s3.put_object(
        Bucket=bucket,
        Key=filename,
        Body=image_bytes,
        ContentType='image/jpeg',
        ACL='public-read',
    )

    bucket_url = config('AWS_S3_BUCKET_URL')
    return f'{bucket_url}/{filename}'


def generate_and_upload(prompt, width=768, height=512):
    raw = generate_image(prompt, width, height)
    compressed = compress_image(raw)
    url = upload_to_s3(compressed)
    return url

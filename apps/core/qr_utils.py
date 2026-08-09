import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


def generate_qr_image(data, filename="qr.png"):
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name=filename)
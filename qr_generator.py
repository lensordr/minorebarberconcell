import qrcode
from io import BytesIO
import base64

def generate_qr_code(url="https://minore-barbershop.onrender.com/book"):
    """Generate QR code for the booking URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save as PNG
    img.save("static/qr_code.png")
    print(f"QR code saved as static/qr_code.png")
    print(f"QR code points to: {url}")
    
    return "static/qr_code.png"

if __name__ == "__main__":
    generate_qr_code()
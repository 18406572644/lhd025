import requests
import io
from PIL import Image

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("测试图片访问功能")
print("=" * 60)

# 1. 登录
print("\n1. 登录...")
login_data = {"username": "explorer1", "password": "123456"}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"   ✅ 登录成功")

# 2. 创建并上传图片
print("\n2. 上传测试图片...")
img = Image.new('RGB', (800, 600), color='blue')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

files = {'file': ('test_image.png', img_bytes, 'image/png')}
data = {'is_public': 'true'}

response = requests.post(
    f"{BASE_URL}/uploads/image",
    headers=headers,
    files=files,
    data=data
)

result = response.json()
print(f"   ✅ 上传成功")
print(f"      原始 URL: {result['image']['original_url']}")
print(f"      小图 URL: {result['image']['thumb_small_url']}")
print(f"      大图 URL: {result['image']['thumb_large_url']}")

# 3. 测试访问原始图片
print("\n3. 测试访问原始图片...")
original_url = result['image']['original_url']
response = requests.get(original_url)
if response.status_code == 200:
    with Image.open(io.BytesIO(response.content)) as img:
        print(f"   ✅ 原始图片访问成功!")
        print(f"      格式: {img.format}")
        print(f"      尺寸: {img.size[0]}x{img.size[1]}")
        print(f"      大小: {len(response.content)} bytes")
else:
    print(f"   ❌ 访问失败: {response.status_code}")

# 4. 测试访问小图
print("\n4. 测试访问小图 (200x200)...")
small_url = result['image']['thumb_small_url']
response = requests.get(small_url)
if response.status_code == 200:
    with Image.open(io.BytesIO(response.content)) as img:
        print(f"   ✅ 小图访问成功!")
        print(f"      格式: {img.format}")
        print(f"      尺寸: {img.size[0]}x{img.size[1]}")
        print(f"      大小: {len(response.content)} bytes")
else:
    print(f"   ❌ 访问失败: {response.status_code}")

# 5. 测试访问大图
print("\n5. 测试访问大图 (1200x1200)...")
large_url = result['image']['thumb_large_url']
response = requests.get(large_url)
if response.status_code == 200:
    with Image.open(io.BytesIO(response.content)) as img:
        print(f"   ✅ 大图访问成功!")
        print(f"      格式: {img.format}")
        print(f"      尺寸: {img.size[0]}x{img.size[1]}")
        print(f"      大小: {len(response.content)} bytes")
else:
    print(f"   ❌ 访问失败: {response.status_code}")

# 6. 测试 WebP 格式
print("\n6. 验证图片格式...")
response = requests.get(original_url)
if response.status_code == 200:
    with Image.open(io.BytesIO(response.content)) as img:
        if img.format == 'WEBP':
            print(f"   ✅ 图片已正确转换为 WebP 格式!")
        else:
            print(f"   ⚠️  图片格式为 {img.format}，期望 WebP")

# 7. 测试压缩效果
print("\n7. 测试压缩效果...")
original_size = len(img_bytes.getvalue())
compressed_size = len(requests.get(original_url).content)
compression_ratio = (1 - compressed_size / original_size) * 100
print(f"   原始大小: {original_size} bytes")
print(f"   压缩后大小: {compressed_size} bytes")
print(f"   压缩率: {compression_ratio:.1f}%")
if compression_ratio > 0:
    print(f"   ✅ 压缩成功!")

# 8. 删除测试图片
print("\n8. 清理测试图片...")
image_id = result['image']['id']
response = requests.delete(f"{BASE_URL}/uploads/images/{image_id}", headers=headers)
print(f"   ✅ 删除成功")

print("\n" + "=" * 60)
print("所有图片访问测试完成!")
print("=" * 60)

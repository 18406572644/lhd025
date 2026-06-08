import requests
import json
import io
from PIL import Image

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("测试图片上传与管理系统")
print("=" * 60)

# 1. 测试健康检查
print("\n1. 测试健康检查...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   ✅ 健康检查成功: {response.json()}")
except Exception as e:
    print(f"   ❌ 健康检查失败: {e}")

# 2. 登录获取 token
print("\n2. 登录获取 token...")
try:
    login_data = {
        "username": "explorer1",
        "password": "123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   ✅ 登录成功")
    else:
        print(f"   ❌ 登录失败: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ 登录异常: {e}")
    exit(1)

# 3. 创建测试图片
print("\n3. 创建测试图片...")
try:
    img = Image.new('RGB', (800, 600), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    print(f"   ✅ 创建测试图片成功 (800x600 PNG)")
except Exception as e:
    print(f"   ❌ 创建测试图片失败: {e}")
    exit(1)

# 4. 测试图片上传
print("\n4. 测试图片上传...")
try:
    files = {
        'file': ('test_image.png', img_bytes, 'image/png')
    }
    data = {'is_public': 'true'}
    
    response = requests.post(
        f"{BASE_URL}/uploads/image",
        headers=headers,
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 图片上传成功!")
        print(f"      图片 ID: {result['image']['id']}")
        print(f"      文件名: {result['image']['filename']}")
        print(f"      原始 URL: {result['image']['original_url']}")
        print(f"      小图 URL: {result['image']['thumb_small_url']}")
        print(f"      中图 URL: {result['image']['thumb_medium_url']}")
        print(f"      大图 URL: {result['image']['thumb_large_url']}")
        print(f"      尺寸: {result['image']['width']}x{result['image']['height']}")
        print(f"      格式: {result['image']['format']}")
        print(f"      文件大小: {result['image']['file_size']} bytes")
        image_id = result['image']['id']
    else:
        print(f"   ❌ 图片上传失败: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ 图片上传异常: {e}")
    exit(1)

# 5. 测试获取我的图片列表
print("\n5. 测试获取我的图片列表...")
try:
    response = requests.get(f"{BASE_URL}/uploads/images", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 获取图片列表成功!")
        print(f"      总数: {result['total']}")
        print(f"      当前页: {result['page']}")
        print(f"      每页数量: {result['page_size']}")
        print(f"      图片数量: {len(result['items'])}")
    else:
        print(f"   ❌ 获取图片列表失败: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ❌ 获取图片列表异常: {e}")

# 6. 测试获取单个图片信息
print("\n6. 测试获取单个图片信息...")
try:
    response = requests.get(f"{BASE_URL}/uploads/images/{image_id}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 获取图片信息成功!")
        print(f"      图片 ID: {result['id']}")
        print(f"      文件名: {result['original_filename']}")
        print(f"      是否公开: {result['is_public']}")
    else:
        print(f"   ❌ 获取图片信息失败: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ❌ 获取图片信息异常: {e}")

# 7. 测试图片访问（原始图片）
print("\n7. 测试图片访问...")
try:
    # 检查 uploads 目录下是否有文件
    import os
    upload_dir = "D:/lhd025/backend/uploads"
    if os.path.exists(upload_dir):
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                if file.endswith('.webp'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, upload_dir).replace('\\', '/')
                    print(f"   找到文件: {rel_path}")
                    
                    # 测试访问
                    response = requests.get(f"http://localhost:8000/uploads/{rel_path}")
                    if response.status_code == 200:
                        print(f"   ✅ 图片访问成功! ({len(response.content)} bytes)")
                        with Image.open(io.BytesIO(response.content)) as img:
                            print(f"      图片格式: {img.format}")
                            print(f"      图片尺寸: {img.size[0]}x{img.size[1]}")
                    else:
                        print(f"   ❌ 图片访问失败: {response.status_code}")
                    break
            break
except Exception as e:
    print(f"   ❌ 图片访问测试异常: {e}")

# 8. 测试删除图片
print("\n8. 测试删除图片...")
try:
    response = requests.delete(f"{BASE_URL}/uploads/images/{image_id}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 图片删除成功: {result['message']}")
    else:
        print(f"   ❌ 图片删除失败: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ❌ 图片删除异常: {e}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)

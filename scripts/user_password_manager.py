#!/usr/bin/env python3
"""
用户密码管理工具
支持通过命令行修改用户密码、创建用户、删除用户等操作
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

def get_users_file_path() -> Path:
    """获取用户配置文件路径"""
    # 从脚本目录向上查找web目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    users_file = project_root / "web" / "config" / "users.json"
    return users_file

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict:
    """加载用户配置"""
    users_file = get_users_file_path()
    
    if not users_file.exists():
        print(f"❌ 用户配置文件不存在: {users_file}")
        return {}
    
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载用户配置失败: {e}")
        return {}

def save_users(users: Dict) -> bool:
    """保存用户配置"""
    users_file = get_users_file_path()
    
    try:
        # 确保目录存在
        users_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 用户配置已保存到: {users_file}")
        return True
    except Exception as e:
        print(f"❌ 保存用户配置失败: {e}")
        return False

def list_users():
    """列出所有用户"""
    users = load_users()
    
    if not users:
        print("📝 没有找到用户")
        return
    
    print("📋 用户列表:")
    print("-" * 60)
    print(f"{'用户名':<15} {'角色':<10} {'权限':<30} {'创建时间'}")
    print("-" * 60)
    
    for username, user_info in users.items():
        role = user_info.get('role', 'unknown')
        permissions = ', '.join(user_info.get('permissions', []))
        created_at = user_info.get('created_at', 0)
        created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_at))
        
        print(f"{username:<15} {role:<10} {permissions:<30} {created_time}")

def change_password(username: str, new_password: str) -> bool:
    """修改用户密码"""
    users = load_users()
    
    if username not in users:
        print(f"❌ 用户不存在: {username}")
        return False
    
    # 更新密码哈希
    users[username]['password_hash'] = hash_password(new_password)
    
    if save_users(users):
        print(f"✅ 用户 {username} 的密码已成功修改")
        return True
    else:
        return False

def create_user(username: str, password: str, role: str = "user", permissions: list = None) -> bool:
    """创建新用户"""
    users = load_users()
    
    if username in users:
        print(f"❌ 用户已存在: {username}")
        return False
    
    if permissions is None:
        permissions = ["analysis"] if role == "user" else ["analysis", "config", "admin"]
    
    # 创建新用户
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "permissions": permissions,
        "created_at": time.time()
    }
    
    if save_users(users):
        print(f"✅ 用户 {username} 创建成功")
        print(f"   角色: {role}")
        print(f"   权限: {', '.join(permissions)}")
        return True
    else:
        return False

def delete_user(username: str) -> bool:
    """删除用户"""
    users = load_users()
    
    if username not in users:
        print(f"❌ 用户不存在: {username}")
        return False
    
    # 防止删除最后一个管理员
    admin_count = sum(1 for user in users.values() if user.get('role') == 'admin')
    if users[username].get('role') == 'admin' and admin_count <= 1:
        print(f"❌ 不能删除最后一个管理员用户")
        return False
    
    del users[username]
    
    if save_users(users):
        print(f"✅ 用户 {username} 已删除")
        return True
    else:
        return False

def reset_to_default():
    """重置为默认用户配置"""
    default_users = {
        "admin": {
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "permissions": ["analysis", "config", "admin"],
            "created_at": time.time()
        },
        "user": {
            "password_hash": hash_password("user123"),
            "role": "user", 
            "permissions": ["analysis"],
            "created_at": time.time()
        }
    }
    
    if save_users(default_users):
        print("✅ 用户配置已重置为默认设置")
        print("   默认用户:")
        print("   - admin / admin123 (管理员)")
        print("   - user / user123 (普通用户)")
        return True
    else:
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="QuantScope 用户密码管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有用户
  python user_password_manager.py list

  # 修改用户密码
  python user_password_manager.py change-password admin newpassword123

  # 创建新用户
  python user_password_manager.py create-user newuser password123 --role user

  # 删除用户
  python user_password_manager.py delete-user olduser

  # 重置为默认配置
  python user_password_manager.py reset
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出用户命令
    subparsers.add_parser('list', help='列出所有用户')
    
    # 修改密码命令
    change_parser = subparsers.add_parser('change-password', help='修改用户密码')
    change_parser.add_argument('username', help='用户名')
    change_parser.add_argument('password', help='新密码')
    
    # 创建用户命令
    create_parser = subparsers.add_parser('create-user', help='创建新用户')
    create_parser.add_argument('username', help='用户名')
    create_parser.add_argument('password', help='密码')
    create_parser.add_argument('--role', choices=['user', 'admin'], default='user', help='用户角色')
    create_parser.add_argument('--permissions', nargs='+', help='用户权限列表')
    
    # 删除用户命令
    delete_parser = subparsers.add_parser('delete-user', help='删除用户')
    delete_parser.add_argument('username', help='用户名')
    
    # 重置命令
    subparsers.add_parser('reset', help='重置为默认用户配置')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🔧 QuantScope 用户密码管理工具")
    print("=" * 50)
    
    try:
        if args.command == 'list':
            list_users()
        
        elif args.command == 'change-password':
            change_password(args.username, args.password)
        
        elif args.command == 'create-user':
            create_user(args.username, args.password, args.role, args.permissions)
        
        elif args.command == 'delete-user':
            delete_parser = input(f"确认删除用户 '{args.username}'? (y/N): ")
            if delete_parser.lower() == 'y':
                delete_user(args.username)
            else:
                print("❌ 操作已取消")
        
        elif args.command == 'reset':
            confirm = input("确认重置为默认用户配置? 这将删除所有现有用户! (y/N): ")
            if confirm.lower() == 'y':
                reset_to_default()
            else:
                print("❌ 操作已取消")
    
    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
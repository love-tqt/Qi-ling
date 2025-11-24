#!/usr/bin/env python
"""测试dbservice模块导入是否正常工作"""

try:
    from dbservice import DatabaseService
    print("✅ dbservice模块导入成功！")
    print("✅ DatabaseService类可用")
    
    # 测试雪花算法生成
    print("\n测试雪花算法ID生成:")
    try:
        test_id = DatabaseService._generate_snowflake_id()
        print(f"✅ 成功生成雪花ID: {test_id}")
        print(f"✅ 雪花ID类型: {type(test_id)}")
        print(f"✅ 雪花ID长度: {len(bin(test_id))-2} bits")
    except Exception as e:
        print(f"❌ 雪花算法测试失败: {e}")
        
except ImportError as e:
    print(f"❌ dbservice模块导入失败: {e}")
except Exception as e:
    print(f"❌ 未知错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")
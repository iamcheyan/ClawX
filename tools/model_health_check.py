#!/usr/bin/env python3
"""
模型健康检查 - 测试所有可用的 LLM provider
"""
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

def test_opencode_models():
    """测试 Opencode 免费模型"""
    models = [
        "opencode/kimi-k2.5-free",
        "opencode/minimax-m2.1-free",
        "opencode/gpt-5-nano",
        "opencode/trinity-large-preview-free",
        "opencode/glm-4.7-free"
    ]
    
    results = []
    print("\n🧪 Testing Opencode Free Models...")
    print("=" * 50)
    
    for model in models:
        print(f"\n📡 Testing {model}...")
        start = time.time()
        try:
            result = subprocess.run(
                ['/home/tetsuya/.opencode/bin/opencode', 'run', '--model', model],
                input="你好，请用一句话介绍自己",
                capture_output=True,
                text=True,
                timeout=60
            )
            elapsed = time.time() - start
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"   ✅ Success ({elapsed:.1f}s)")
                print(f"   📝 Response: {result.stdout.strip()[:60]}...")
                results.append({
                    "provider": "opencode",
                    "model": model,
                    "success": True,
                    "response_time": elapsed,
                    "response_preview": result.stdout.strip()[:100]
                })
            else:
                print(f"   ❌ Failed: {result.stderr[:80] if result.stderr else 'Empty response'}")
                results.append({
                    "provider": "opencode",
                    "model": model,
                    "success": False,
                    "error": result.stderr[:100] if result.stderr else "Empty response"
                })
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Timeout (>60s)")
            results.append({
                "provider": "opencode",
                "model": model,
                "success": False,
                "error": "Timeout"
            })
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "provider": "opencode",
                "model": model,
                "success": False,
                "error": str(e)[:100]
            })
    
    return results

def save_results(results):
    """保存测试结果"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "healthy": sum(1 for r in results if r["success"]),
        "results": results
    }
    
    # 保存到 model-status.json
    status_path = Path("/home/tetsuya/twitter.openclaw.lcmd/model-status.json")
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    return output

def main():
    print("🚀 Starting Model Health Check...")
    print(f"Time: {datetime.now()}")
    
    # 测试所有模型
    all_results = []
    all_results.extend(test_opencode_models())
    
    # 保存结果
    summary = save_results(all_results)
    
    # 打印摘要
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Total models: {summary['total']}")
    print(f"Healthy: {summary['healthy']} ✅")
    print(f"Failed: {summary['total'] - summary['healthy']} ❌")
    
    print("\n📝 Detailed Results:")
    for r in all_results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['model']}")
        if r["success"]:
            print(f"      Time: {r['response_time']:.1f}s")
        else:
            print(f"      Error: {r.get('error', 'Unknown')[:50]}")
    
    print(f"\n💾 Results saved to: /home/tetsuya/twitter.openclaw.lcmd/model-status.json")
    print("✅ Done!")

if __name__ == "__main__":
    main()

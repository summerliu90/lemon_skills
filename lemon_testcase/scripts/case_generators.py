#!/usr/bin/env python3
"""Deterministic generators for functional, UI, performance and automation cases."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any

def module_prefix(area: str) -> str:
    text = str(area)
    known = {"登录功能":"DL", "登录模块":"DL", "注册功能":"ZC", "注册模块":"ZC", "用户模块":"YH", "订单模块":"DD"}
    if text in known: return known[text]
    if "登录" in text: return "DL"
    if "注册" in text: return "ZC"
    latin = "".join(x for x in text.upper() if x.isalnum())
    return (latin[:2] or "TC")

def base(name, area, kind, number, tags, source, priority="P2", flow_type="正常流程", test_method="正向验证", **extra):
    return {"case_id":f"{module_prefix(area)}_{number:03d}","name":name,"area":area,"kind":kind,"flow_type":flow_type,"test_method":test_method,"priority":priority,"preconditions":["测试环境可用"],"actions":["准备测试数据","执行被测功能"],"assertions":["系统返回可观察且符合需求的结果"],"data":{},"source_refs":[source],"tags":tags,"notes":[],"automation_candidate":kind in ("functional","api","automation"),**extra}

def _terms(text): return [x for x in re.split(r"[。；;\n]",text) if x.strip()]

def functional(text: str, area="功能模块", source="需求文档"):
    rules=_terms(text); cases=[]; n=1
    for rule in rules or ["核心业务功能"]:
        short=rule.strip()[:60]
        for method,tags,priority,action,assertion,flow_type,test_method in [
            ("非法输入",["negative","equivalence"],"P1",[f"输入不满足{short}约束的数据"],["系统拒绝请求并给出可理解的错误反馈"],"异常流程","非法输入"),
            ("正常流程",["positive","scenario"],"P0",[f"执行{short}"],[f"{short}完成，结果与验收标准一致"],"正常流程","正向验证"),
            ("边界值",["negative","boundary"],"P1",[f"输入{short}相关约束的临界值及临界前后值"],["边界值处理符合规则，超出范围时不产生错误数据"],"正常流程","边界值"),
            ("状态与恢复",["state","recovery"],"P2",["重复执行操作或在中断后重新执行"],["操作具备正确幂等/恢复行为，数据状态保持一致"],"异常流程","恢复验证")] :
            c=base(short,area,"functional",n,tags,source,priority,flow_type=flow_type,test_method=test_method); c["actions"]=action; c["assertions"]=assertion; cases.append(c); n+=1
    order={"正常流程":0,"异常流程":1}
    method_order={"正向验证":0,"场景法":1,"等价类":2,"边界值":3,"非法输入":0,"异常流程":1,"权限异常":2,"状态迁移":3,"恢复验证":4}
    cases.sort(key=lambda c: (order.get(c.get("flow_type"), 9), method_order.get(c.get("test_method"), 9)))
    for i, case in enumerate(cases, 1): case["case_id"]=f"{module_prefix(area)}_{i:03d}"
    return {"schema_version":"1.0","project":"","source":{"kind":"prd","files":[source]},"assumptions":[],"testcases":cases}

def ui(area="页面", source="设计稿"):
    matrix=[("布局与文本",["visual"],"检查布局、文字、对齐、截断和滚动", "页面结构与设计意图一致"),("交互组件",["interaction"],"操作按钮、表单、导航、弹窗和键盘焦点", "控件状态、反馈和焦点顺序正确"),("加载与空态",["state","loading"],"模拟加载、空数据和慢响应", "加载指示、空态和恢复入口清晰"),("错误与禁用",["negative","error"],"触发校验、网络错误和权限不足", "错误提示准确，禁用控件不可提交"),("响应式",["responsive"],"检查桌面、平板、移动尺寸和方向变化", "内容不溢出，关键操作可用"),("可访问性",["accessibility"],"使用键盘、辅助技术语义和对比检查", "可聚焦、可读、标签关联且反馈可感知")]
    cases=[]
    for n,(name,tags,action,assertion) in enumerate(matrix,1):
        c=base(name,area,"ui",n,tags,source,"P1",test_method=name,automation_candidate=name not in ("布局与文本","可访问性")); c["actions"]=[action]; c["assertions"]=[assertion]; cases.append(c)
    return {"schema_version":"1.0","project":"","source":{"kind":"ui","files":[source]},"assumptions":[],"testcases":cases}

def performance(area="性能场景", source="性能目标"):
    matrix=[("基线",["baseline"]),("阶梯负载",["load","ramp"]),("峰值流量",["load","peak"]),("长稳运行",["soak"]),("流量突增",["spike"]),("依赖降级",["degradation"]),("恢复验证",["recovery"])]
    cases=[]
    for n,(name,tags) in enumerate(matrix,1):
        flow = "异常流程" if name in ("依赖降级", "恢复验证") else "正常流程"
        c=base(name,area,"performance",n,tags,source,"P1",flow_type=flow,test_method=name,automation_candidate=False); c["preconditions"]=["已确认压测环境和流量上限","SLA 指标待确认或已由项目提供"]; c["actions"]=[f"执行{name}场景","记录 P50/P95/P99、吞吐、错误率和资源指标"]; c["assertions"]=["业务结果正确","性能指标与已确认目标比较，未确认目标不判定为通过"] ; cases.append(c)
    return {"schema_version":"1.0","project":"","source":{"kind":"performance","files":[source]},"assumptions":[],"testcases":cases}

def automation(doc):
    result=json.loads(json.dumps(doc));
    for case in result.get("testcases",[]):
        stable=bool(case.get("assertions")) and not any(x in " ".join(case.get("notes",[])) for x in ("待确认","不稳定")); case["automation_candidate"]=stable; case.setdefault("automation",{}).update({"layer":"api" if case.get("kind")=="api" else "ui" if case.get("kind")=="ui" else "service","data_strategy":"fixture-per-case","wait_strategy":"explicit","isolation":"独立准备和清理","assertion_strategy":"业务结果 + 契约字段"})
    return result

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--type",choices=["functional","ui","performance","automation"],required=True); ap.add_argument("--text",default="核心功能"); ap.add_argument("--output",required=True); ap.add_argument("--area",default="测试模块"); args=ap.parse_args(argv)
    doc=functional(args.text,args.area) if args.type=="functional" else ui(args.area) if args.type=="ui" else performance(args.area) if args.type=="performance" else automation(functional(args.text,args.area))
    Path(args.output).write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"generated {len(doc['testcases'])} cases")
if __name__=="__main__": sys.exit(main())

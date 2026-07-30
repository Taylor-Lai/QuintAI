"""Authoritative built-in template catalog shared by every client."""

from __future__ import annotations


def _template(identifier: str, name: str, category: str, scene: str, fields: list[str]) -> dict[str, object]:
    return {
        "id": f"builtin_{identifier}",
        "name": name,
        "category": category,
        "scene": scene,
        "description": f"适用于{name}相关信息的规范化采集与表格生成。",
        "format": "Excel / 在线表单",
        "tags": [category, scene],
        "fields": [
            {"id": f"field_{index}", "label": label, "key": f"field_{index}", "type": "text", "required": False}
            for index, label in enumerate(fields, start=1)
        ],
        "source": "builtin",
        "editable": False,
    }


BUILTIN_TEMPLATES = [
    _template("contract", "合同信息登记表", "行政办公", "合同管理", ["合同编号", "合同名称", "甲方", "乙方", "签署日期", "生效日期", "到期日期", "合同金额", "负责人", "状态", "归档编号", "备注"]),
    _template("onboarding", "员工入职信息表", "人事管理", "员工档案", ["姓名", "性别", "身份证号", "手机号", "邮箱", "部门", "岗位", "入职日期", "工号", "紧急联系人", "联系地址", "学历", "毕业院校", "开户行", "银行卡号"]),
    _template("expense", "费用报销申请表", "财务管理", "费用报销", ["申请人", "部门", "报销事由", "费用类型", "金额", "发生日期", "票据数量", "审批人", "支付方式", "备注"]),
    _template("purchase", "采购申请汇总表", "供应链", "采购审批", ["申请部门", "申请人", "物品名称", "规格型号", "数量", "预算金额", "用途说明", "申请日期", "供应商建议", "到货日期", "审批意见"]),
    _template("attendance", "会议签到登记表", "行政办公", "活动签到", ["会议名称", "姓名", "单位", "部门", "职务", "手机号", "签到时间", "签字"]),
    _template("grades", "学生成绩登记表", "教育场景", "成绩管理", ["学号", "姓名", "班级", "课程名称", "平时成绩", "期中成绩", "期末成绩", "总评成绩", "教师评语"]),
    _template("medical", "病历信息采集表", "医疗场景", "病历整理", ["姓名", "性别", "年龄", "住院号", "科室", "主诉", "既往史", "诊断结果", "检查结论", "治疗方案", "入院日期", "出院日期", "主治医生", "备注"]),
    _template("project", "项目进度跟踪表", "项目管理", "进度管理", ["项目名称", "阶段名称", "任务名称", "负责人", "开始时间", "截止时间", "完成状态", "优先级", "风险说明", "依赖项", "成果物", "更新时间", "备注"]),
    _template("assets", "固定资产登记表", "财务管理", "资产管理", ["资产编号", "资产名称", "规格型号", "购置日期", "原值", "使用部门", "使用人", "存放地点", "资产状态", "折旧年限", "盘点日期", "备注"]),
]

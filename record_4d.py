import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DATA_FILE = "my_4d_records.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_data(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

class App4D:
    def __init__(self, root):
        self.root = root
        self.root.title("4D 号码记录小助手")
        self.root.geometry("820x500")
        self.records = load_data()

        # 1. 输入区域
        frame_input = ttk.LabelFrame(root, text=" 添加新记录 ", padding=10)
        frame_input.pack(fill="x", padx=10, pady=5)

        # 日期
        ttk.Label(frame_input, text="日期:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ent_date = ttk.Entry(frame_input, width=12)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # 号码
        ttk.Label(frame_input, text="4D号码:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.ent_number = ttk.Entry(frame_input, width=10)
        self.ent_number.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # 公司
        ttk.Label(frame_input, text="博彩公司:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.cmb_company = ttk.Combobox(frame_input, values=["Magnum", "Toto", "Damacai", "STC", "CashSweep", "Sabah88", "Dragon4D"], width=10, state="readonly")
        self.cmb_company.current(0)
        self.cmb_company.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # 玩法输入区域：4个玩法各带一个文本输入框
        ttk.Label(frame_input, text="玩法金额:").grid(row=1, column=0, padx=5, pady=5, sticky="ne")
        
        frame_bets = ttk.Frame(frame_input)
        frame_bets.grid(row=1, column=1, columnspan=5, padx=5, pady=5, sticky="w")

        # Big
        ttk.Label(frame_bets, text="Big:").pack(side="left", padx=(0, 2))
        self.ent_big = ttk.Entry(frame_bets, width=6)
        self.ent_big.pack(side="left", padx=(0, 15))

        # Small
        ttk.Label(frame_bets, text="Small:").pack(side="left", padx=(0, 2))
        self.ent_small = ttk.Entry(frame_bets, width=6)
        self.ent_small.pack(side="left", padx=(0, 15))

        # Ibox
        ttk.Label(frame_bets, text="Ibox:").pack(side="left", padx=(0, 2))
        self.ent_ibox = ttk.Entry(frame_bets, width=6)
        self.ent_ibox.pack(side="left", padx=(0, 15))

        # PM
        ttk.Label(frame_bets, text="PM:").pack(side="left", padx=(0, 2))
        self.ent_pm = ttk.Entry(frame_bets, width=6)
        self.ent_pm.pack(side="left", padx=(0, 5))

        # 备注
        ttk.Label(frame_input, text="备注:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.ent_notes = ttk.Entry(frame_input, width=50)
        self.ent_notes.grid(row=2, column=1, columnspan=5, padx=5, pady=5, sticky="w")

        # 保存按钮
        btn_add = ttk.Button(frame_input, text="保存记录", command=self.add_record)
        btn_add.grid(row=3, column=0, columnspan=6, pady=10)

        # 2. 列表展示区域
        frame_list = ttk.LabelFrame(root, text=" 号码记录列表 ", padding=10)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "date", "number", "company", "bet", "total", "notes")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings", height=10)

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="购买/开奖日期")
        self.tree.heading("number", text="4D号码")
        self.tree.heading("company", text="公司")
        self.tree.heading("bet", text="玩法明细")
        self.tree.heading("total", text="Total")
        self.tree.heading("notes", text="备注")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("number", width=70, anchor="center")
        self.tree.column("company", width=90, anchor="center")
        self.tree.column("bet", width=200, anchor="w")
        self.tree.column("total", width=70, anchor="center")
        self.tree.column("notes", width=120, anchor="w")

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 3. 操作按钮区域
        frame_actions = ttk.Frame(root)
        frame_actions.pack(fill="x", padx=10, pady=5)
        
        btn_delete = ttk.Button(frame_actions, text="选中删除", command=self.delete_record)
        btn_delete.pack(side="right")

        self.refresh_table()

    def add_record(self):
        date_val = self.ent_date.get().strip()
        num_val = self.ent_number.get().strip()
        company_val = self.cmb_company.get().strip()
        notes_val = self.ent_notes.get().strip()

        if not num_val.isdigit() or len(num_val) != 4:
            messagebox.showerror("输入错误", "4D 号码必须是 4 位纯数字！")
            return

        # 获取各玩法的输入值并转换为浮点数/整数累加
        big_val = self.ent_big.get().strip()
        small_val = self.ent_small.get().strip()
        ibox_val = self.ent_ibox.get().strip()
        pm_val = self.ent_pm.get().strip()

        selected_bets = []
        total_amount = 0.0

        try:
            if big_val:
                val = float(big_val)
                selected_bets.append(f"Big: {big_val}")
                total_amount += val
            if small_val:
                val = float(small_val)
                selected_bets.append(f"Small: {small_val}")
                total_amount += val
            if ibox_val:
                val = float(ibox_val)
                selected_bets.append(f"Ibox: {ibox_val}")
                total_amount += val
            if pm_val:
                val = float(pm_val)
                selected_bets.append(f"PM: {pm_val}")
                total_amount += val
        except ValueError:
            messagebox.showerror("输入错误", "玩法金额必须是有效的数字！")
            return

        if not selected_bets:
            messagebox.showwarning("提示", "请至少在一个玩法输入框中填入金额或数量！")
            return

        bet_str = " | ".join(selected_bets)

        record = {
            "id": len(self.records) + 1,
            "date": date_val,
            "number": num_val,
            "company": company_val if company_val else "通用",
            "bet_type": bet_str,
            "total": total_amount,
            "notes": notes_val if notes_val else "无"
        }

        self.records.append(record)
        save_data(self.records)
        self.refresh_table()
        
        # 清空输入框
        self.ent_number.delete(0, tk.END)
        self.ent_big.delete(0, tk.END)
        self.ent_small.delete(0, tk.END)
        self.ent_ibox.delete(0, tk.END)
        self.ent_pm.delete(0, tk.END)
        self.ent_notes.delete(0, tk.END)
        
        messagebox.showinfo("成功", f"号码 [{num_val}] 已保存，总计: {total_amount}！")

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        sorted_records = sorted(self.records, key=lambda x: x.get("date", ""), reverse=True)
        for r in sorted_records:
            # 兼容旧数据没有 total 字段的情况
            total_val = r.get("total", 0)
            self.tree.insert("", "end", values=(r["id"], r.get("date", ""), r["number"], r["company"], r["bet_type"], total_val, r["notes"]))

    def delete_record(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("提示", "请先在列表中选中要删除的记录！")
            return
        
        item_values = self.tree.item(selected_item, "values")
        record_id = int(item_values[0])

        self.records = [r for r in self.records if r["id"] != record_id]
        
        for idx, r in enumerate(self.records, start=1):
            r["id"] = idx
            
        save_data(self.records)
        self.refresh_table()
        messagebox.showinfo("成功", "记录已成功删除！")

if __name__ == "__main__":
    root = tk.Tk()
    app = App4D(root)
    root.mainloop()
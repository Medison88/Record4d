import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from tkcalendar import DateEntry

DATA_FILE = "passup_records.json"

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

class PassupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Passup Record - Desktop App")
        self.root.geometry("950x720")
        
        self.records = load_data()
        self.editing_id = None  # 用于记录当前正在修改的记录 ID (None 表示新增)
        
        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        # 1. 输入表单区域
        self.form_frame = ttk.LabelFrame(self.root, text=" ➕ Add New Passup Record (Ready for New) ", padding=15)
        self.form_frame.pack(fill="x", padx=10, pady=10)

        # 第一行：Date 弹窗日历选择器 和 Terminal 选择
        ttk.Label(self.form_frame, text="Date:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.date_entry = DateEntry(
            self.form_frame, 
            width=12, 
            background='darkblue', 
            foreground='white', 
            borderwidth=2, 
            date_pattern='yyyy-mm-dd'
        )
        self.date_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.date_entry.bind("<<DateEntrySelected>>", lambda event: self.refresh_table())

        ttk.Label(self.form_frame, text="Terminal:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.terminal_var = tk.StringVar(value="Terminal 1")
        terminal_cb = ttk.Combobox(self.form_frame, textvariable=self.terminal_var, values=["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 4"], state="readonly", width=15)
        terminal_cb.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        # 金额输入字段
        fields = [
            ("Payment ($):", "pay_dollar"),
            ("Payment (Q):", "pay_q"),
            ("Unpaid Ticket:", "unpaid"),
            ("Cash:", "cash"),
            ("E-Pay:", "epay")
        ]

        self.entries = {}
        for idx, (label_text, key) in enumerate(fields):
            r = 1 if idx < 3 else 2
            c = (idx % 3) * 2
            ttk.Label(self.form_frame, text=label_text).grid(row=r, column=c, sticky="w", padx=5, pady=5)
            ent = ttk.Entry(self.form_frame, width=15)
            ent.grid(row=r, column=c+1, sticky="w", padx=5, pady=5)
            self.entries[key] = ent

        # 备注
        ttk.Label(self.form_frame, text="Note:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.note_ent = ttk.Entry(self.form_frame, width=45)
        self.note_ent.grid(row=3, column=1, columnspan=5, sticky="w", padx=5, pady=5)

        # 操作按钮区
        btn_action_frame = ttk.Frame(self.form_frame)
        btn_action_frame.grid(row=4, column=0, columnspan=4, pady=10, sticky="w")

        # 智能保存/修改按钮
        self.save_btn = ttk.Button(btn_action_frame, text="💾 Save Record", command=self.save_or_update_record)
        self.save_btn.pack(side="left", padx=5)

        # 取消修改按钮
        self.cancel_btn = ttk.Button(btn_action_frame, text="❌ Cancel Edit", command=self.cancel_edit)
        self.cancel_btn.pack(side="left", padx=5)
        self.cancel_btn.state(["disabled"])  # 默认未在编辑时禁用

        # 2. 列表展示区域
        table_frame = ttk.LabelFrame(self.root, text=" 📋 Records History (Double click any row to edit) ", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("ID", "Date", "Terminal", "Payment($)", "Payment(Q)", "Unpaid", "Cash", "E-Pay", "Total", "Note")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        self.tree.column("Note", width=130)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定双击事件：双击表格某一行直接加载到上方进行修改
        self.tree.bind("<Double-1>", self.load_record_for_editing)

        # 3. 最底部：当日统计共计栏 (Summary Bar)
        summary_frame = ttk.LabelFrame(self.root, text=" 📊 Daily Summary (Total for Selected Date) ", padding=10)
        summary_frame.pack(fill="x", padx=10, pady=5)

        self.summary_labels = {}
        summary_items = [
            ("Payment($)", "pay_dollar"),
            ("Payment(Q)", "pay_q"),
            ("Unpaid", "unpaid"),
            ("Cash", "cash"),
            ("E-Pay", "epay"),
            ("Total", "total")
        ]

        for idx, (title, key) in enumerate(summary_items):
            lbl_title = ttk.Label(summary_frame, text=f"{title}:", font=("Arial", 9, "bold"))
            lbl_title.grid(row=0, column=idx*2, sticky="e", padx=5, pady=2)
            
            lbl_val = ttk.Label(summary_frame, text="0.00", font=("Arial", 9), foreground="blue")
            lbl_val.grid(row=0, column=idx*2+1, sticky="w", padx=5, pady=2)
            self.summary_labels[key] = lbl_val

        # 4. 底部删除操作区
        del_frame = ttk.Frame(self.root)
        del_frame.pack(fill="x", padx=10, pady=5)
        del_btn = ttk.Button(del_frame, text="🗑️ Delete Selected Record", command=self.delete_record)
        del_btn.pack(side="left")

    def load_record_for_editing(self, event):
        """双击表格行时，将数据回填到上方表单，准备修改"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        vals = self.tree.item(item, "values")
        rec_id = int(vals[0])

        # 在总记录中找到这条数据
        target = next((r for r in self.records if r["id"] == rec_id), None)
        if not target:
            return

        self.editing_id = rec_id  # 标记当前正在修改的 ID
        
        # 回填表单数据
        self.date_entry.set_date(target["date"])
        self.terminal_var.set(target["terminal"])
        self.entries["pay_dollar"].delete(0, tk.END)
        self.entries["pay_dollar"].insert(0, str(target["pay_dollar"]))
        
        self.entries["pay_q"].delete(0, tk.END)
        self.entries["pay_q"].insert(0, str(target["pay_q"]))
        
        self.entries["unpaid"].delete(0, tk.END)
        self.entries["unpaid"].insert(0, str(target["unpaid"]))
        
        self.entries["cash"].delete(0, tk.END)
        self.entries["cash"].insert(0, str(target["cash"]))
        
        self.entries["epay"].delete(0, tk.END)
        self.entries["epay"].insert(0, str(target["epay"]))
        
        self.note_ent.delete(0, tk.END)
        self.note_ent.insert(0, target["note"])

        # 更改界面提示与按钮状态
        self.form_frame.config(text=f" ✏️ Edit Record (ID: {rec_id}) ")
        self.save_btn.config(text="🔄 Update Record")
        self.cancel_btn.state(["!disabled"])

    def cancel_edit(self):
        """取消修改状态，恢复新增状态"""
        self.editing_id = None
        self.form_frame.config(text=" ➕ Add New Passup Record (Ready for New) ")
        self.save_btn.config(text="💾 Save Record")
        self.cancel_btn.state(["disabled"])
        
        # 清空输入框
        for ent in self.entries.values():
            ent.delete(0, tk.END)
        self.note_ent.delete(0, tk.END)

    def save_or_update_record(self):
        date_str = self.date_entry.get().strip()
        if not date_str:
            messagebox.showerror("Error", "Please select a date!")
            return

        try:
            data_vals = {}
            total = 0.0
            for k, ent in self.entries.items():
                val_str = ent.get().strip()
                val = float(val_str) if val_str else 0.0
                data_vals[k] = val
                if k in ["pay_dollar", "unpaid", "cash", "epay"]:
                    total += val
        except ValueError:
            messagebox.showerror("Error", "All financial amounts must be valid numbers!")
            return

        if self.editing_id is None:
            # 1. 新增记录逻辑
            new_record = {
                "id": len(self.records) + 1,
                "date": date_str,
                "terminal": self.terminal_var.get(),
                "pay_dollar": data_vals["pay_dollar"],
                "pay_q": data_vals["pay_q"],
                "unpaid": data_vals["unpaid"],
                "cash": data_vals["cash"],
                "epay": data_vals["epay"],
                "total": total,
                "note": self.note_ent.get().strip() or "No Record"
            }
            self.records.append(new_record)
            msg = "Record saved successfully!"
        else:
            # 2. 更新修改记录逻辑
            for r in self.records:
                if r["id"] == self.editing_id:
                    r["date"] = date_str
                    r["terminal"] = self.terminal_var.get()
                    r["pay_dollar"] = data_vals["pay_dollar"]
                    r["pay_q"] = data_vals["pay_q"]
                    r["unpaid"] = data_vals["unpaid"]
                    r["cash"] = data_vals["cash"]
                    r["epay"] = data_vals["epay"]
                    r["total"] = total
                    r["note"] = self.note_ent.get().strip() or "No Record"
                    break
            msg = f"Record ID {self.editing_id} updated successfully!"
            self.cancel_edit()  # 重置编辑状态

        save_data(self.records)
        self.refresh_table()
        
        # 清空金额和备注输入框
        for ent in self.entries.values():
            ent.delete(0, tk.END)
        self.note_ent.delete(0, tk.END)
        messagebox.showinfo("Success", f"{msg} Total: {total:.2f}")

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        selected_date = self.date_entry.get().strip()
        filtered_records = [r for r in self.records if r.get("date") == selected_date]
        
        totals = {
            "pay_dollar": 0.0,
            "pay_q": 0.0,
            "unpaid": 0.0,
            "cash": 0.0,
            "epay": 0.0,
            "total": 0.0
        }

        for r in filtered_records:
            self.tree.insert("", "end", values=(
                r["id"], r["date"], r["terminal"], 
                r["pay_dollar"], r["pay_q"], r["unpaid"], 
                r["cash"], r["epay"], r["total"], r["note"]
            ))
            for k in totals.keys():
                totals[k] += float(r.get(k, 0.0))

        for k, lbl in self.summary_labels.items():
            lbl.config(text=f"{totals[k]:.2f}")

    def delete_record(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a record from the table to delete!")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected record?"):
            for item in selected_items:
                vals = self.tree.item(item, "values")
                rec_id = int(vals[0])
                self.records = [r for r in self.records if r["id"] != rec_id]
            
            # 重新编号
            for idx, r in enumerate(self.records, start=1):
                r["id"] = idx
            
            save_data(self.records)
            self.refresh_table()
            messagebox.showinfo("Success", "Record deleted successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = PassupApp(root)
    root.mainloop()
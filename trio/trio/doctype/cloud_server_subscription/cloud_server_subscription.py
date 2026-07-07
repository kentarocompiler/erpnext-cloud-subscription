# Copyright (c) 2026, kentaro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CloudServerSubscription(Document):
	def on_submit(self):
		"""ฟังก์ชันนี้จะทำงานอัตโนมัติเมื่อผู้ใช้กดปุ่ม Submit เอกสาร"""
		
		company = self.company if hasattr(self, 'company') else frappe.defaults.get_user_default("company")
		posting_date = self.posting_date if hasattr(self, 'posting_date') else frappe.utils.today()
		
		# ดึง Cost Center เริ่มต้นของบริษัทมาใช้งานอัตโนมัติ
		cost_center = frappe.get_cached_value('Company', company, 'default_cost_center')
		if not cost_center:
			cost_center = f"Main - {frappe.get_cached_value('Company', company, 'abbr')}"

		amount = self.total_amount 

		if not amount or amount <= 0:
			frappe.throw("กรุณาระบุจำนวนเงินที่ถูกต้องก่อนทำการ Submit")

		debit_account = "IT Expenses - S"    
		credit_account = "Cash - S"

		# บันทึกบัญชีขาที่ 1: Debit ค่าใช้จ่าย
		make_gl_entry(
			company=company,
			posting_date=posting_date,
			account=debit_account,
			cost_center=cost_center,
			debit=amount,
			credit=0,
			voucher_type=self.doctype,
			voucher_no=self.name,
			against=credit_account,
			remarks=f"บันทึกบัญชีอัตโนมัติ: Cloud Server Subscription เลขที่ {self.name}"
		)

		# บันทึกบัญชีขาที่ 2: Credit เงินฝากธนาคาร
		make_gl_entry(
			company=company,
			posting_date=posting_date,
			account=credit_account,
			cost_center=cost_center,
			debit=0,
			credit=amount,
			voucher_type=self.doctype,
			voucher_no=self.name,
			against=debit_account,
			remarks=f"บันทึกบัญชีอัตโนมัติ: Cloud Server Subscription เลขที่ {self.name}"
		)

		frappe.msgprint("ระบบได้ทำการบันทึกบัญชีคู่ (GL Entry) เรียบร้อยแล้ว!")

	def on_cancel(self):
		"""ฟังก์ชันนี้จะทำงานเมื่อกด Cancel เอกสาร -> ให้ไปลบ GL Entry ที่เคยสร้างไว้"""
		frappe.db.sql("""
			DELETE FROM `tabGL Entry` 
			WHERE voucher_type=%s AND voucher_no=%s
		""", (self.doctype, self.name))
		frappe.msgprint("ยกเลิกการบันทึกบัญชี (GL Entry) สำเร็จ")


def make_gl_entry(**args):
	"""ฟังก์ชันช่วยสร้างเอกสาร GL Entry เข้าฐานข้อมูล"""
	gl_entry = frappe.new_doc("GL Entry")
	gl_entry.update(args)
	gl_entry.insert(ignore_permissions=True)
	gl_entry.submit()
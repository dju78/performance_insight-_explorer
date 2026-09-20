"""Generate 5 Multi-Sector Synthetic Datasets for Performance Insight Explorer demo & onboarding."""
import numpy as np
import pandas as pd
import os

os.makedirs("sample_data", exist_ok=True)
np.random.seed(42)

# 1. Healthcare Service Performance (Emergency & Elective Care Flow)
dates_hc = pd.date_range(start="2025-01-01", periods=12, freq="ME")
trusts = ["North General NHS Trust", "St. Jude Hospital", "Mercy Metropolitan Trust", "East Valley Hospital"]
hc_rows = []
for t in trusts:
    base_inflow = 1200 if "North" in t else (950 if "St." in t else 1100)
    for d in dates_hc:
        inflow = int(np.random.normal(base_inflow, 80))
        fte = round(np.random.uniform(22.0, 28.0), 1)
        # 4-hour standard target: 95%
        four_hr_target = 95.0
        four_hr_actual = round(np.random.uniform(72.0, 91.0) if "East" not in t else np.random.uniform(88.0, 96.0), 1)
        completions = int(inflow * (four_hr_actual / 100.0) + np.random.normal(50, 20))
        wait_mins = round(np.random.uniform(180, 310) if four_hr_actual < 85 else np.random.uniform(120, 210), 1)
        bed_occupancy_pct = round(np.random.uniform(86.0, 98.0), 1)
        closing_backlog = max(20, int(inflow - completions + np.random.normal(150, 30)))
        
        hc_rows.append({
            "reporting_month": d.strftime("%Y-%m"),
            "hospital_trust": t,
            "clinical_division": "Urgent & Emergency Care",
            "cases_received": inflow,
            "cases_completed": completions,
            "target_sla_pct": four_hr_target,
            "actual_sla_pct": four_hr_actual,
            "avg_wait_time_mins": wait_mins,
            "bed_occupancy_pct": bed_occupancy_pct,
            "clinical_fte": fte,
            "closing_backlog": closing_backlog
        })
df_hc = pd.DataFrame(hc_rows)
df_hc.to_csv("sample_data/healthcare_service_performance.csv", index=False)

# 2. Sales & Commercial Performance
teams_sales = ["Enterprise Tech", "Mid-Market EMEA", "Commercial APAC", "Public Sector UK"]
sales_rows = []
for tm in teams_sales:
    target_rev = 450000 if "Enterprise" in tm else 280000
    for d in dates_hc:
        fte = round(np.random.uniform(6.0, 10.0), 1)
        leads = int(np.random.normal(180, 25))
        conversion_rate = round(np.random.uniform(12.0, 26.0), 1)
        deals_closed = int(leads * (conversion_rate / 100.0))
        deal_size = np.random.normal(25000 if "Enterprise" in tm else 12000, 3000)
        actual_rev = int(deals_closed * deal_size)
        sales_cost = int(fte * 6500 + np.random.normal(15000, 2000))
        
        sales_rows.append({
            "reporting_period": d.strftime("%Y-%m"),
            "sales_team": tm,
            "region": "Global" if "Enterprise" in tm else tm.split()[-1],
            "leads_received": leads,
            "deals_completed": deals_closed,
            "conversion_rate_pct": conversion_rate,
            "actual_revenue": actual_rev,
            "target_revenue": target_rev,
            "sales_operating_cost": sales_cost,
            "sales_fte": fte
        })
df_sales = pd.DataFrame(sales_rows)
df_sales.to_csv("sample_data/sales_revenue_performance.csv", index=False)

# 3. Customer Service Operations
cs_teams = ["Tier 1 Digital Support", "Tier 2 Technical Desk", "Billing & Subscriptions", "VIP Accounts"]
cs_rows = []
for tm in cs_teams:
    for d in dates_hc:
        tickets_in = int(np.random.normal(2400 if "Tier 1" in tm else 800, 150))
        fte = round(np.random.uniform(14.0, 20.0) if "Tier 1" in tm else np.random.uniform(5.0, 8.0), 1)
        fcr_target = 80.0
        fcr_actual = round(np.random.uniform(70.0, 88.0), 1)
        csat_score = round(np.random.uniform(3.8, 4.8), 2)
        tickets_out = int(tickets_in * np.random.uniform(0.92, 1.05))
        avg_handle_time = round(np.random.uniform(6.5, 14.0), 1)
        closing_wip = max(10, int(np.random.normal(120, 25)))
        
        cs_rows.append({
            "reporting_month": d.strftime("%Y-%m"),
            "support_team": tm,
            "channel": "Omnichannel",
            "tickets_received": tickets_in,
            "tickets_completed": tickets_out,
            "first_contact_resolution_pct": fcr_actual,
            "target_fcr_pct": fcr_target,
            "csat_score_out_of_5": csat_score,
            "avg_handle_time_mins": avg_handle_time,
            "support_fte": fte,
            "closing_backlog": closing_wip
        })
df_cs = pd.DataFrame(cs_rows)
df_cs.to_csv("sample_data/customer_service_operations.csv", index=False)

# 4. Human Resources & Workforce Performance
depts_hr = ["Engineering", "Product & Design", "Customer Experience", "Sales & Marketing", "Corporate & Finance"]
hr_rows = []
for dept in depts_hr:
    base_headcount = 140 if "Engineering" in dept else (80 if "Sales" in dept else 45)
    for d in dates_hc:
        headcount = int(np.random.normal(base_headcount, 4))
        turnover_rate = round(np.random.uniform(0.8, 2.5), 2)
        absence_days = int(np.random.normal(headcount * 0.4, 6))
        training_hours_per_emp = round(np.random.uniform(2.5, 6.0), 1)
        open_vacancies = int(np.random.normal(headcount * 0.08, 2))
        recruitment_cost = int(open_vacancies * np.random.normal(4500, 400))
        
        hr_rows.append({
            "reporting_month": d.strftime("%Y-%m"),
            "department": dept,
            "active_headcount": headcount,
            "monthly_turnover_pct": turnover_rate,
            "target_turnover_ceiling_pct": 1.5,
            "total_absence_days": absence_days,
            "avg_training_hours": training_hours_per_emp,
            "open_vacancies": max(0, open_vacancies),
            "recruitment_spend": max(0, recruitment_cost)
        })
df_hr = pd.DataFrame(hr_rows)
df_hr.to_csv("sample_data/workforce_hr_performance.csv", index=False)

# 5. Local Government Service Delivery
gov_services = ["Development & Planning", "Waste & Environmental Services", "Revenues & Benefits", "Adult Social Care Assessments"]
gov_rows = []
for s in gov_services:
    target_sla = 80.0 if "Planning" in s else (90.0 if "Benefits" in s else 85.0)
    for d in dates_hc:
        apps_in = int(np.random.normal(420, 40))
        apps_out = int(apps_in * np.random.uniform(0.88, 1.04))
        sla_actual = round(np.random.uniform(target_sla - 15.0, target_sla + 8.0), 1)
        officer_fte = round(np.random.uniform(8.0, 14.0), 1)
        avg_processing_days = round(np.random.uniform(28.0, 62.0), 1)
        pending_caseload = max(30, int(np.random.normal(210, 30)))
        
        gov_rows.append({
            "reporting_month": d.strftime("%Y-%m"),
            "directorate": s,
            "service_area": "Civic Operations",
            "cases_received": apps_in,
            "cases_completed": apps_out,
            "actual_sla_attainment_pct": sla_actual,
            "target_sla_pct": target_sla,
            "avg_processing_days": avg_processing_days,
            "case_officer_fte": officer_fte,
            "closing_caseload": pending_caseload
        })
df_gov = pd.DataFrame(gov_rows)
df_gov.to_csv("sample_data/local_government_service_delivery.csv", index=False)

print("Generated 5 multi-sector synthetic datasets successfully.")

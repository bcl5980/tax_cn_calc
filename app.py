from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

# City-specific parameters (centralized configuration)
CITY_PARAMS = {
    '北京': {
        'base_amount': 11761,
        'min_wage': 2540,  # 最低工资标准
        'company_pension': 16.0,
        'company_medical': 9.8,
        'company_unemployment': 0.5,
        'company_injury': 0.2,
        'company_housing_fund': 12.0,
        'personal_pension': 8.0,
        'personal_medical': 2.0,
        'personal_unemployment': 0.5,
        'personal_housing_fund': 12.0
    },
    '上海': {
        'base_amount': 12307,
        'min_wage': 2740,  # 最低工资标准
        'company_pension': 16.0,
        'company_medical': 9.5,
        'company_unemployment': 0.5,
        'company_injury': 0.16,
        'company_housing_fund': 7.0,
        'personal_pension': 8.0,
        'personal_medical': 2.0,
        'personal_unemployment': 0.5,
        'personal_housing_fund': 7.0
    },
}

def calculate_income_tax(income):
    """Calculate income tax for annual income using progressive tax brackets"""
    if income <= 0:
        return 0
    elif income <= 36000:
        return income * 0.03
    elif income <= 144000:
        return income * 0.1 - 2520
    elif income <= 300000:
        return income * 0.2 - 16920
    elif income <= 420000:
        return income * 0.25 - 31920
    elif income <= 660000:
        return income * 0.3 - 52920
    elif income <= 960000:
        return income * 0.35 - 85920
    else:
        return income * 0.45 - 181920

def calculate_monthly_base(annual_salary, base_amount):
    """Calculate monthly social security base with 60%-300% limits"""
    monthly_base = annual_salary / 12
    if monthly_base < base_amount * 0.6:
        monthly_base = base_amount * 0.6
    elif monthly_base > base_amount * 3:
        monthly_base = base_amount * 3
    return monthly_base

def calculate_min_wage_supplement(monthly_take_home, min_wage):
    """Calculate minimum wage supplement if needed"""
    if monthly_take_home < min_wage:
        return min_wage - monthly_take_home
    return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_city_params')
def get_city_params():
    """Get city-specific parameters"""
    return jsonify(CITY_PARAMS)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    
    annual_salary = float(data['annual_salary'])
    base_amount = float(data['base_amount'])
    min_wage = float(data.get('min_wage', 0))  # 最低工资标准
    
    # Social security rates
    company_rates = {
        'pension': float(data['company_pension']) / 100,
        'medical': float(data['company_medical']) / 100,
        'unemployment': float(data['company_unemployment']) / 100,
        'injury': float(data['company_injury']) / 100,
        'housing_fund': float(data['company_housing_fund']) / 100
    }
    
    personal_rates = {
        'pension': float(data['personal_pension']) / 100,
        'medical': float(data['personal_medical']) / 100,
        'unemployment': float(data['personal_unemployment']) / 100,
        'housing_fund': float(data['personal_housing_fund']) / 100
    }
    
    # Calculate monthly base with limits
    monthly_base = calculate_monthly_base(annual_salary, base_amount)
    
    # Calculate social security deductions
    company_total = monthly_base * sum(company_rates.values()) * 12
    personal_social_security = monthly_base * sum(personal_rates.values()) * 12
    
    # Calculate pre-tax income after social security
    pre_tax_income = annual_salary - personal_social_security
    
    # Calculate income tax
    taxable_income = max(0, pre_tax_income - 60000)  # 5000 * 12 = 60000
    income_tax = calculate_income_tax(taxable_income)
    
    # Calculate final take-home pay
    take_home_pay = pre_tax_income - income_tax
    monthly_take_home = take_home_pay / 12
    
    # Calculate minimum wage supplement if needed
    min_wage_supplement_monthly = calculate_min_wage_supplement(monthly_take_home, min_wage)
    min_wage_supplement_annual = min_wage_supplement_monthly * 12
    
    # Adjust take-home pay with minimum wage guarantee
    final_take_home_pay = take_home_pay + min_wage_supplement_annual
    final_monthly_take_home = final_take_home_pay / 12
    
    # Calculate the three tax rates (including minimum wage supplement in company cost)
    total_company_cost = annual_salary + company_total + min_wage_supplement_annual
    personal_contribution = monthly_base * personal_rates['housing_fund'] * 12
    
    rate1 = final_take_home_pay / annual_salary * 100
    rate2 = (final_take_home_pay + personal_contribution) / total_company_cost * 100
    rate3 = final_take_home_pay / total_company_cost * 100
    
    # Calculate personal take-home including housing fund
    housing_fund_personal = monthly_base * personal_rates['housing_fund'] * 12
    personal_take_home = final_take_home_pay + housing_fund_personal
    
    result = {
        'monthly_base': monthly_base,
        'company_total': company_total,
        'personal_social_security': personal_social_security,
        'pre_tax_income': pre_tax_income,
        'income_tax': income_tax,
        'take_home_pay': take_home_pay,
        'min_wage_supplement': min_wage_supplement_annual,
        'final_take_home_pay': final_take_home_pay,
        'monthly_take_home': final_monthly_take_home,
        'personal_take_home': personal_take_home,
        'total_company_cost': total_company_cost,
        'rate1': rate1,
        'rate2': rate2,
        'rate3': rate3
    }
    
    return jsonify(result)

def calculate_bonus_tax(bonus, monthly_salary):
    """Calculate tax for year-end bonus using separate taxation method"""
    if bonus <= 0:
        return 0
        
    # Calculate average monthly bonus
    avg_monthly_bonus = bonus / 12
    
    # Determine tax rate based on combined monthly income
    monthly_income = monthly_salary + avg_monthly_bonus
    
    # Progressive tax brackets for bonus calculation
    if monthly_income <= 3000:
        rate, quick_deduction = 0.03, 0
    elif monthly_income <= 12000:
        rate, quick_deduction = 0.1, 210
    elif monthly_income <= 25000:
        rate, quick_deduction = 0.2, 1410
    elif monthly_income <= 35000:
        rate, quick_deduction = 0.25, 2660
    elif monthly_income <= 55000:
        rate, quick_deduction = 0.3, 4410
    elif monthly_income <= 80000:
        rate, quick_deduction = 0.35, 7160
    else:
        rate, quick_deduction = 0.45, 15160
    
    return bonus * rate - quick_deduction

@app.route('/optimize_year_end', methods=['POST'])
def optimize_year_end():
    data = request.json
    annual_salary = float(data['annual_salary'])
    base_amount = float(data.get('base_amount', 8000))
    min_wage = float(data.get('min_wage', 0))
    
    # Get social security parameters
    company_rates = {
        'pension': float(data.get('company_pension', 16)) / 100,
        'medical': float(data.get('company_medical', 9.8)) / 100,
        'unemployment': float(data.get('company_unemployment', 0.5)) / 100,
        'injury': float(data.get('company_injury', 0.2)) / 100,
        'housing_fund': float(data.get('company_housing_fund', 5)) / 100
    }
    
    personal_rates = {
        'pension': float(data.get('personal_pension', 8)) / 100,
        'medical': float(data.get('personal_medical', 2)) / 100,
        'unemployment': float(data.get('personal_unemployment', 0.5)) / 100,
        'housing_fund': float(data.get('personal_housing_fund', 5)) / 100
    }
    
    def get_total_tax_and_cost(bonus):
        """Calculate total tax and company cost for given bonus amount"""
        if bonus < 0 or bonus > annual_salary:
            return float('inf'), float('inf')
        
        monthly_salary = max(0, (annual_salary - bonus) / 12)
        monthly_base = calculate_monthly_base(monthly_salary * 12, base_amount)
        
        # Calculate social security
        personal_ss = monthly_base * sum(personal_rates.values()) * 12
        company_ss = monthly_base * sum(company_rates.values()) * 12
        
        # Calculate taxes
        annual_salary_after_ss = monthly_salary * 12 - personal_ss
        taxable_income = max(0, annual_salary_after_ss - 60000)
        salary_tax = calculate_income_tax(taxable_income)
        bonus_tax = calculate_bonus_tax(bonus, monthly_salary)
        
        # Calculate take-home and minimum wage supplement
        take_home_pay = annual_salary_after_ss - salary_tax - bonus_tax
        monthly_take_home = take_home_pay / 12
        min_wage_supplement_monthly = calculate_min_wage_supplement(monthly_take_home, min_wage)
        min_wage_supplement_annual = min_wage_supplement_monthly * 12
        
        total_tax = salary_tax + bonus_tax
        total_company_cost = annual_salary + company_ss + min_wage_supplement_annual
        
        return total_tax, total_company_cost, min_wage_supplement_annual

    def get_discrete_points():
        """Get discrete critical points based on tax brackets"""
        points = [0, annual_salary]
        
        # Tax bracket boundaries
        brackets = [36000, 144000, 300000, 420000, 660000, 960000]
        for bracket in brackets:
            if 0 < bracket < annual_salary:
                points.append(bracket)
        
        # Test intervals of 10000
        for i in range(0, int(annual_salary), 10000):
            points.append(i)
        
        return list(set([max(0, min(annual_salary, int(p))) for p in points]))

    # Find optimal bonus amount (minimize total cost to company)
    discrete_points = get_discrete_points()
    min_cost = float('inf')
    best_bonus = 0
    best_supplement = 0
    
    # Test discrete points
    for bonus in discrete_points:
        tax, cost, supplement = get_total_tax_and_cost(bonus)
        if cost < min_cost:
            min_cost = cost
            best_bonus = bonus
            best_supplement = supplement
    
    # Test nearby values around best discrete point
    nearby = [best_bonus - 5000, best_bonus - 2000, best_bonus - 1000, 
              best_bonus, best_bonus + 1000, best_bonus + 2000, best_bonus + 5000]
    
    for bonus in nearby:
        if 0 <= bonus <= annual_salary:
            tax, cost, supplement = get_total_tax_and_cost(bonus)
            if cost < min_cost:
                min_cost = cost
                best_bonus = bonus
                best_supplement = supplement
    
    # Calculate final breakdown
    monthly_salary = (annual_salary - best_bonus) / 12
    monthly_base = calculate_monthly_base(monthly_salary * 12, base_amount)
    
    personal_ss = monthly_base * sum(personal_rates.values()) * 12
    annual_salary_after_ss = monthly_salary * 12 - personal_ss
    taxable_income = max(0, annual_salary_after_ss - 60000)
    
    salary_tax = calculate_income_tax(taxable_income)
    bonus_tax = calculate_bonus_tax(best_bonus, monthly_salary)
    
    # Calculate take-home pay including housing fund
    housing_fund_personal = monthly_base * personal_rates['housing_fund'] * 12
    take_home_pay = annual_salary_after_ss - salary_tax - bonus_tax
    final_take_home_pay = take_home_pay + best_supplement
    personal_take_home = final_take_home_pay + housing_fund_personal
    
    # Calculate baseline (no bonus)
    baseline_tax, baseline_cost, baseline_supplement = get_total_tax_and_cost(0)
    
    best_breakdown = {
        'bonus': best_bonus,
        'monthly_salary': monthly_salary,
        'total_tax': salary_tax + bonus_tax,
        'salary_tax': salary_tax,
        'bonus_tax': bonus_tax,
        'personal_social_security': personal_ss,
        'take_home_pay': take_home_pay,
        'min_wage_supplement': best_supplement,
        'final_take_home_pay': final_take_home_pay,
        'personal_take_home': personal_take_home,
        'total_company_cost': min_cost,
        'cost_savings': baseline_cost - min_cost,
        'baseline_cost': baseline_cost
    }
    
    return jsonify(best_breakdown)

if __name__ == '__main__':
    app.run(debug=True)
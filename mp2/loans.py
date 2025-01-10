
import json
import zipfile
import csv
import io

class Applicant:
    
    race_lookup = {
        "1": "American Indian or Alaska Native",
        "2": "Asian",
        "3": "Black or African American",
        "4": "Native Hawaiian or Other Pacific Islander",
        "5": "White",
        "21": "Asian Indian",
        "22": "Chinese",
        "23": "Filipino",
        "24": "Japanese",
        "25": "Korean",
        "26": "Vietnamese",
        "27": "Other Asian",
        "41": "Native Hawaiian",
        "42": "Guamanian or Chamorro",
        "43": "Samoan",
        "44": "Other Pacific Islander"
    }
    
    def __init__(self, age, race):
        self.age = age
        self.race = set()
        for r in race:
            if r in self.race_lookup:
                self.race.add(self.race_lookup[r])
                
    def __repr__(self):
        race_list = [race for race in self.race]
        return f"Applicant('{self.age}', {race_list})"
    
    def __lt__(self, other):
        return self.lower_age() < other.lower_age()
    
    def lower_age(self):
        age = self.age.replace('<', '').replace('>', '') 
        if '-' in age:  
            return int(age.split('-')[0])
        else:
            return int(age)
    
class Loan:
 
    def __init__(self, values):
        self.loan_amount = self.convert_to_float(values.get("loan_amount", "-1"))
        self.property_value = self.convert_to_float(values.get("property_value", "-1"))
        self.interest_rate = self.convert_to_float(values.get("interest_rate", "-1"))
        self.applicants = self.create_applicants(values)
        
    def __str__(self):
        return f"<Loan: {self.interest_rate}% on ${self.property_value} with {len(self.applicants)} applicant(s)>"

    def __repr__(self):
        return f"<Loan: {self.interest_rate}% on ${self.property_value} with {len(self.applicants)} applicant(s)>"

    def convert_to_float(self, value):
        if value.lower() == "na" or value.lower() == "exempt":
            return -1
        else:
            return float(value)

    def create_applicants(self, values):
        applicants = []
        applicant_age = values.get("applicant_age", "-1")
        applicant_race = [values.get(f"applicant_race-{i}", "-1") for i in range(1, 6)]
        applicants.append(Applicant(applicant_age, applicant_race))

        co_applicant_age = values.get("co-applicant_age", "-1")
        if co_applicant_age != "9999":
            co_applicant_race = [values.get(f"co-applicant_race-{i}", "-1") for i in range(1, 6)]
            applicants.append(Applicant(co_applicant_age, co_applicant_race))
        return applicants
    
    def yearly_amounts(self, yearly_payment):
        # TODO: assert interest and amount are positive
        self.yearly_payment = yearly_payment
        amt = self.loan_amount
        interest_decimal = self.interest_rate / 100

        while amt > 0:
            yield amt
            # TODO: add interest rate multiplied by amt to amt
            amt += (interest_decimal * amt)
            # TODO: subtract yearly payment from amt
            amt -= self.yearly_payment

class Bank:
    
    def __init__(self, name):
        with open('banks.json', 'r') as file:
            bank_data = json.load(file)
        
        for bank_info in bank_data:
            if bank_info['name'] == name:
                self.name = name
                self.lei = bank_info['lei']
                return 
        
        raise ValueError(f"Bank '{name}' not found in the database.")
        
    def __getitem__(self, key):
        return self.loans[key]

    def __len__(self):
        return len(self.loans)

    def load_from_zip(self, path):
        with zipfile.ZipFile(path, 'r') as zip_file:
            csv_filename = zip_file.namelist()[0] 
            with zip_file.open(csv_filename, 'r') as csv_file:
                csv_reader = csv.DictReader(io.TextIOWrapper(csv_file, 'utf-8'))
                
                loans = []
                
                for row in csv_reader:
                    if row.get('lei') == self.lei:
                        loan = Loan(row)  
                        loans.append(loan)
                
                self.loans = loans
                
    def average_interest_rate(self):
        total_interest_rate = 0
        count = 0
        for loan in self.loans:
            if loan.interest_rate != None:
                total_interest_rate += loan.interest_rate
                count += 1
        
        if count == 0:
            return 0
        
        return total_interest_rate / count
    
    def num_applicants(self):
        total_applicants = sum(len(loan.applicants) for loan in self.loans)
        total_loans = len(self.loans)
        return total_applicants / total_loans
    
    def ages_dict(self):
        age_dict = {}
        
        for loan in self.loans:
            for applicant in loan.applicants:
                if applicant.age not in age_dict:
                    age_dict[applicant.age] = 0
                age_dict[applicant.age] += 1
        
        sorted_age_dict = dict(sorted(age_dict.items()))
        return sorted_age_dict
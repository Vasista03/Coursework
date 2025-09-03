def simple_interest(principal, rate, time):
    interest = (principal * rate * time) / 100
    return interest
principal=float(input("Enter the principal amount: "))
rate=float(input("Enter the rate of interest: "))   
time=float(input("Enter the duration in years: "))
sim_int=simple_interest(principal, rate, time)
print("The simple interest is:", sim_int)

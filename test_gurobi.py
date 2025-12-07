import gurobipy as gp
from gurobipy import GRB

# Create a simple test model
model = gp.Model("test_model")

# Add a variable x >= 0
x = model.addVar(name="x", lb=0)

# Set the objective: maximize x
model.setObjective(x, GRB.MAXIMIZE)

# Add a constraint: x <= 5
model.addConstr(x <= 5, name="c1")

# Optimize the model
model.optimize()

# Print the result
print(f"Optimal x: {x.X}")

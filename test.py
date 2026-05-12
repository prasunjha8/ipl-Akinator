best_col, best_score = None, -1
ig = 0.5
if ig > best_score:
    best_score = best_col, ig
    best_col = "something"
ig = 0.6
print(type(best_score))
try:
    if ig > best_score:
        pass
except Exception as e:
    print(e)

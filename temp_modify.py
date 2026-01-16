with open('routes/projet18_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Modifier la ligne 3599 (index 3598) pour page 1
lines[3598] = '                        ligne_underscore = "_" * 28  # Augmenté de 27 à 28 caractères (+0,1cm supplémentaire) pour les lignes horaires\n'

# Modifier la ligne 4133 (index 4132) pour page 2
lines[4132] = '                        ligne_underscore = "_" * 28  # Augmenté de 27 à 28 caractères (+0,1cm supplémentaire) pour les lignes horaires\n'

with open('routes/projet18_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Modified lines 3599 and 4133 to 28 characters')









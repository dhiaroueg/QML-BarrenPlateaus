"""Paramètres centralisés du protocole expérimental."""

SEED = 42

# Circuit (inspiré de McClean et al. 2018) : couche fixe RY(pi/4) sur chaque qubit,
# puis L couches [rotation aléatoire RX/RY/RZ par qubit + CZ en « brickwork »].
PREP_ANGLE = 3.141592653589793 / 4

# Initialisations comparées
INITS = ("uniform", "small", "identity_block")
SMALL_SIGMA = 0.1  # écart-type de l'initialisation « petits angles »

# Fonctions de coût comparées (Cerezo et al. 2021) : les deux sont calculées sur
# les MÊMES circuits, ce qui rend la comparaison appariée.
COSTS = ("global", "local")

# Grilles par défaut (mode complet)
QUBITS = tuple(range(2, 13))           # 2 à 12 qubits
DEPTHS_QUBIT_SWEEP = (2, 10, 30)       # profondeurs de l'expérience 01
DEPTH_SWEEP_QUBITS = (4, 8)            # nombres de qubits de l'expérience 02
DEPTH_SWEEP_LAYERS = (1, 2, 4, 6, 10, 16, 24, 40)
INIT_STUDY_DEPTH = 10                  # profondeur de l'expérience 03 (paire)
N_SAMPLES = 300                        # initialisations aléatoires par configuration
BOOTSTRAP = 500                        # rééchantillonnages pour l'IC de la variance

# Grilles réduites (mode --quick) : vérifier le flux, pas conclure
QUICK_QUBITS = (2, 3, 4, 5, 6)
QUICK_DEPTHS = (2, 6)
QUICK_DEPTH_SWEEP_QUBITS = (4,)
QUICK_DEPTH_SWEEP_LAYERS = (1, 2, 4, 8)
QUICK_SAMPLES = 40
QUICK_BOOTSTRAP = 100

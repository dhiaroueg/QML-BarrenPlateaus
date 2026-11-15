# QML-BarrenPlateaus

**Entraînabilité des circuits quantiques variationnels : étude numérique des barren plateaus**

Étude expérimentale, reproductible et testée, de la façon dont la **variance du gradient** d'un circuit variationnel évolue avec le nombre de qubits, la profondeur, l'initialisation des paramètres et le type de fonction de coût (globale ou locale).

> Il s'agit de la **reproduction rigoureuse d'un phénomène connu** (McClean et al. 2018 ; Cerezo et al. 2021 ; Grant et al. 2019), pas d'une découverte. Sa valeur est méthodologique : protocole propre, gradients vérifiés, intervalles de confiance, limites discutées. Voir la section « Limites ».

## Question de recherche

Comment la variance de ∂C/∂θ évolue-t-elle avec **(i)** le nombre de qubits n, **(ii)** la profondeur L, **(iii)** l'initialisation, **(iv)** le coût global ou local ?

## Montage expérimental

**Circuit** (McClean et al. 2018) : une couche fixe `RY(π/4)` sur chaque qubit, puis L couches. Chaque couche applique, sur chaque qubit, une rotation `RX`, `RY` ou `RZ` tirée au hasard (paramètre entraînable), puis des `CZ` en « brickwork » (paires (0,1),(2,3)… aux couches paires, (1,2),(3,4)… aux couches impaires).

**Coûts** (Cerezo et al. 2021), calculés sur les **mêmes circuits** à partir des probabilités de la base de calcul, ce qui rend la comparaison appariée :

- global : `C_G = 1 − P(|0…0⟩)`
- local : `C_L = 1 − (1/n) Σ_j P(qubit j = 0)`

**Gradient** : règle de décalage de paramètre (`dC/dθ = [C(θ+π/2) − C(θ−π/2)]/2`), **exacte** car les mesures sont analytiques (`shots=None`) et les deux coûts sont linéaires en probabilités. Le paramètre dérivé est celui de la première couche, premier qubit.

**Initialisations comparées**

| Nom | Description |
|---|---|
| `uniform` | θ ~ U[0, 2π) : circuit aléatoire (régime des barren plateaus) |
| `small` | θ ~ N(0, σ²), σ = 0,1 : couches entraînables proches de l'identité |
| `identity_block` | Grant et al. 2019 : la seconde moitié du circuit est l'inverse exacte de la première, le circuit complet vaut l'identité (les angles de la seconde moitié sont figés lors du calcul du gradient) |

**Statistiques** : variance non biaisée sur N initialisations (300 par défaut), intervalle de confiance à 95 % par bootstrap, ajustement de `log10 Var = a + b·n` (pente, facteur par qubit, R²).

## Installation (Windows / PowerShell, Python 3.11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Commandes

```powershell
python -m pytest tests -q             # 10 tests de correction (quelques secondes)
python run_all.py --quick             # vérification du flux (moins de 2 min), PAS de conclusion
python run_all.py                     # protocole complet (10 à 20 min sur 1 cœur selon la machine)
python run_all.py --workers 4         # idem, en parallèle
python run_all.py --samples 500 --seed 7   # plus d'échantillons / autre graine
```

Chaque expérience peut aussi être lancée seule : `python experiments/01_variance_vs_qubits.py`, `02_variance_vs_depth.py`, `03_initialization.py`, puis `python experiments/04_make_figures.py` pour régénérer figures et ajustements sans recalcul.

## Structure

```text
src/bp/config.py        grilles et paramètres centralisés
src/bp/circuits.py      circuit, coûts global/local, gradient par parameter-shift
src/bp/sweep.py         échantillonnage reproductible, export CSV
src/bp/stats.py         variance + bootstrap, ajustement exponentiel
experiments/01..03      les trois expériences
experiments/04          figures et decay_fits.json
tests/                  vérification du gradient (vs rétropropagation), bloc identité, etc.
results/metrics/        CSV et JSON produits
results/figures/        figures produites
```

## Vérifications intégrées (tests)

- le gradient par décalage de paramètre **coïncide à 1e-8** avec la rétropropagation, pour l'initialisation uniforme et pour le bloc identité ;
- le circuit « bloc identité » laisse exactement l'état préparé inchangé ;
- les coûts d'un état produit connu sont retrouvés analytiquement ;
- les probabilités sont normalisées, les résultats sont reproductibles à graine fixée, l'ajustement exponentiel retrouve un taux connu.

## Résultats obtenus (graine 42, 300 initialisations, PennyLane 0.45.1)

Ces chiffres proviennent d'une exécution complète du protocole fourni dans ce dépôt ; **relancez-le sur votre machine** pour les confirmer avant de les citer. Les fichiers bruts sont dans `results/metrics/`.

**Décroissance avec n (initialisation uniforme)** : facteur multiplicatif de la variance par qubit supplémentaire, ajusté sur n = 2…12.

| Profondeur L | Coût global | Coût local |
|---|---|---|
| 2 | ×0,37 (R² 0,98) | ×0,71 (R² 0,94) |
| 10 | ×0,31 (R² 0,99) | ×0,69 (R² 0,91) |
| 30 | ×0,26 (R² 1,00) | ×0,60 (R² 0,90) |

Exemple (L = 30) : variance du coût global passant de 2,1e-2 (n = 2) à 2,2e-8 (n = 12), contre 1,3e-2 à 4,4e-5 pour le coût local.

**Initialisation (L = 10)** : pour le coût global, la variance à n = 12 vaut 2,5e-7 en uniforme contre 8,1e-4 avec bloc identité, soit environ 3 000 fois plus ; le facteur par qubit passe de ×0,31 à ×0,73. Pour le coût local, les trois initialisations donnent des courbes très proches (×0,69 à ×0,72).

**Profondeur (n = 8)** : la variance du coût global chute d'environ un facteur 35 entre L = 1 et L = 6, puis reste entre 6e-6 et 1e-5 jusqu'à L = 40. Celle du coût local continue de décroître sur toute la plage (de 1,0e-3 à 7,8e-5).

### Lecture prudente

- Les résultats sont **qualitativement cohérents** avec la littérature : décroissance exponentielle de la variance avec n pour le coût global, atténuation avec un coût local ou une initialisation proche de l'identité.
- Le coût local **n'élimine pas** la décroissance dans cette expérience : il la ralentit fortement (×0,6 à ×0,7 par qubit contre ×0,26 à ×0,37). Cela reste compatible avec le résultat de Cerezo et al., qui garantit l'entraînabilité du coût local pour des circuits **peu profonds**, et ici L ≥ 10 n'est pas peu profond pour n ≤ 12.
- Les ajustements exponentiels sont faits sur n = 2…12 seulement : un R² élevé n'établit pas une loi asymptotique.

## Limites

1. **Petite échelle** : 12 qubits au maximum, une seule graine principale. Pour une conclusion robuste, répéter sur plusieurs graines et reporter la dispersion.
2. **Un seul paramètre dérivé** (première couche, premier qubit). Les gradients d'autres paramètres peuvent différer (effet de cône de lumière).
3. **Une seule architecture** (RX/RY/RZ aléatoires + CZ brickwork) et un seul coût local (somme de projecteurs à 1 qubit).
4. **Initialisations `small` et `identity_block`** : leur « variance » ne mesure presque que l'aléa sur le *type* de portes, puisque les angles sont presque fixés ; elle n'a donc pas le même sens que pour `uniform` (distribution sur des circuits aléatoires). Les deux courbes coïncident presque, ce qui est attendu. Le facteur ×0,7 par qubit qui subsiste pour le coût global pourrait venir de la couche fixe `RY(π/4)`, dont le recouvrement avec |0…0⟩ vaut `cos²(π/8)^n` : **hypothèse non testée** (voir pistes).
5. **Pas de bruit, pas de tirs finis** : les gradients sont exacts. Les barren plateaus induits par le bruit (Wang et al. 2021) ne sont pas étudiés ici.

## Pistes d'extension

- Faire varier `PREP_ANGLE` pour tester l'hypothèse de la limite 4.
- Dériver plusieurs paramètres (premier, milieu, dernier) et comparer.
- Ajouter le bruit dépolarisant (`default.mixed`) : lien direct avec le dépôt AutoQML-Noise.
- Mesurer l'expressibilité du circuit (distance au 2-design) et la relier à la variance (Holmes et al. 2022).
- Ajouter l'entraînement réel (descente de gradient) à partir des différentes initialisations et comparer les vitesses de convergence.

## Si vous mentionnez ce projet sur un CV

Décrivez ce que **vous** avez fait et mesuré : le protocole, les vérifications (test contre rétropropagation), les résultats de **votre** exécution (en indiquant graine, nombre d'échantillons, nombre maximal de qubits) et les limites. Ne présentez pas ce travail comme une découverte : c'est une reproduction méthodique d'un phénomène connu.

## Références (à vérifier avant citation)

1. J. R. McClean et al., « Barren plateaus in quantum neural network training landscapes », *Nature Communications* 9, 4812 (2018).
2. M. Cerezo et al., « Cost function dependent barren plateaus in shallow parametrized quantum circuits », *Nature Communications* 12, 1791 (2021).
3. E. Grant et al., « An initialization strategy for addressing barren plateaus in parametrized quantum circuits », *Quantum* 3, 214 (2019).
4. Z. Holmes et al., « Connecting ansatz expressibility to gradient magnitudes and barren plateaus », *PRX Quantum* 3, 010313 (2022).
5. S. Wang et al., « Noise-induced barren plateaus in variational quantum algorithms », *Nature Communications* 12, 6961 (2021).
6. PennyLane, documentation : https://docs.pennylane.ai

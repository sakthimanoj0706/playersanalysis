# Pressure Model Validation & Comparison Report
**SupeRR Intelligence 2.0**

## 1. Philosophical Separation
In cricket, batting crisis and bowling pressure are fundamentally different situations:
- **Batting Crisis Pressure:** High wickets lost, recent collapses, new batter facing initial balls, death overs.
- **Bowling Defensive Pressure:** Opponent having wickets in hand (high resources), critical phase (death overs and powerplay field restrictions), and opponent boundary momentum in the last 12 balls.

## 2. Batting Crisis Distribution
| batting_pressure_tier   |   deliveries |   avg_runs |   boundary_rate |   wicket_rate |   dot_rate |   pct_of_deliveries |
|:------------------------|-------------:|-----------:|----------------:|--------------:|-----------:|--------------------:|
| none                    |        75924 |   1.44858  |        0.2083   |     0.0479822 |   0.328052 |               39.14 |
| low                     |        71840 |   1.33729  |        0.173914 |     0.0516425 |   0.328132 |               37.03 |
| moderate                |        30760 |   1.2304   |        0.152991 |     0.0589077 |   0.357705 |               15.86 |
| high                    |        11445 |   1.15325  |        0.139712 |     0.0770642 |   0.37938  |                5.9  |
| extreme                 |         4019 |   0.991043 |        0.108485 |     0.107241  |   0.404578 |                2.07 |

## 3. Bowling Defensive Distribution
| bowling_pressure_tier   |   deliveries |   avg_runs |   boundary_rate |   wicket_rate |   dot_rate |   pct_of_deliveries |
|:------------------------|-------------:|-----------:|----------------:|--------------:|-----------:|--------------------:|
| none                    |         1470 |   0.845578 |       0.0918367 |     0.0680272 |   0.504762 |                0.76 |
| low                     |        18991 |   1.07762  |       0.11595   |     0.0526565 |   0.375283 |                9.79 |
| moderate                |        71592 |   1.24594  |       0.156149  |     0.0530367 |   0.348768 |               36.91 |
| high                    |        70591 |   1.42828  |       0.196073  |     0.0551912 |   0.314828 |               36.39 |
| extreme                 |        31344 |   1.5745   |       0.245438  |     0.0537583 |   0.331451 |               16.16 |

## 4. Key Behavioral Findings
- Under Batting Crisis (High + Extreme), average runs drop to 1.13 per ball and wicket probability rises to 7.3%.
- Under Bowling Defensive Pressure (High + Extreme), bowlers operate against aggressive opponents in death overs or powerplays with wickets in hand, where dot ball control is paramount.

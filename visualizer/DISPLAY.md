# Muzieksysteem

## Werking Paneel
### Initialisatie
Voor het sturen van pixels moet je eerst `":00"` sturen.
### Pixel 
Elk ledje heeft een groen en een rood component. Als deze beide aanstaan krijg je (uiteraard) oranje.

Elke 2 bits sturen een ledje aan. De eerste bit hiervan stuurt het groene component aan en het tweede bit het rode.

Voorbeeld voor 4 ledjes:

| bit | led | kleur |
|-----|-----|-------|
|  1  |  1  | groen |
|  2  |  1  | rood  |
|  3  |  2  | groen |
|  4  |  2  | rood  |
|  5  |  3  | groen |
|  6  |  3  | rood  |
|  7  |  4  | groen |
|  8  |  4  | rood  |
# Mecánicas verificadas de Crafter

Verificación directa en el código fuente de `crafter` (`C:\Users\diego\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages\crafter\`).

## 1. ¿Se puede girar sin moverse?
**Sí.**  
En `crafter/objects.py:174-177`:
```python
  def _move(self, direction):
    directions = dict(left=(-1, 0), right=(+1, 0), up=(0, -1), down=(0, +1))
    self.facing = directions[direction]
    self.move(self.facing)
```
La propiedad `self.facing` se actualiza inmediatamente a la dirección solicitada antes de llamar a `self.move(self.facing)`. Si `self.move` devuelve `False` (por ejemplo porque la casilla destino está bloqueada por piedra, árbol, agua u otra criatura), la posición `self.pos` no cambia, pero la orientación `self.facing` sí queda modificada.

## 2. ¿El zombi ataca en diagonal?
**No.** (Contradice el supuesto preventivo del plan).  
En `crafter/objects.py:302-303`:
```python
    dist = self.distance(self.player)
    if dist <= 1:
```
La función `self.distance` está definida en `crafter/objects.py:49-52`:
```python
  def distance(self, target):
    if hasattr(target, 'pos'):
      target = target.pos
    return np.abs(target - self.pos).sum()
```
Calcula la **distancia Manhattan** ($|\Delta x| + |\Delta y|$). En diagonal, $|\Delta x| = 1$ y $|\Delta y| = 1$, por lo que la distancia es $1 + 1 = 2$. Como el zombi solo ataca si `dist <= 1`, **no puede atacar en diagonal**; requiere adyacencia ortogonal (arriba, abajo, izquierda, derecha).

## 3. ¿Colocar piedra va a la casilla de enfrente?
**Sí.**  
En `crafter/objects.py:100` y `crafter/objects.py:231-242`:
```python
    target = (self.pos[0] + self.facing[0], self.pos[1] + self.facing[1])
    ...
    elif action.startswith('place_'):
      self._place(action[len('place_'):], target, material)
```
El objetivo de colocación `target` se calcula sumando `self.facing` a la posición actual del jugador. Además, en `crafter/constants.py:place['stone']`:
```python
{'type': 'material',
 'uses': {'stone': 1},
 'where': ['grass', 'sand', 'path', 'water', 'lava']}
```
Se puede colocar sobre `grass`, `sand`, `path`, `water` y `lava`. Al colocarla, la casilla destino pasa a ser de material `'stone'`.

## 4. ¿Minar una piedra colocada la devuelve al inventario?
**Sí.**  
En `crafter/constants.py:collect['stone']` y `crafter/objects.py:214-230`:
```python
'stone': {'leaves': 'path', 'receive': {'stone': 1}, 'require': {'wood_pickaxe': 1}}
```
En `crafter/objects.py:225-228`:
```python
    self.world[target] = info['leaves']
    if self.random.uniform() <= info.get('probability', 1):
      for name, amount in info['receive'].items():
        self.inventory[name] += amount
```
No existe diferenciación entre piedra generada por el mapa y piedra colocada por el jugador: ambas tienen material `'stone'`. Al minarla con `action == 'do'` teniendo un pico de madera (`wood_pickaxe >= 1`), la casilla se convierte en `'path'` y el inventario recibe `stone: 1`.

## 5. ¿Los zombis pueden aparecer dentro de un recinto cerrado?
**No.**  
En `crafter/env.py:143-147` y `crafter/env.py:163-174`:
```python
    self._balance_object(
        chunk, objs, objects.Zombie, 'grass', 6, 0, 0.3, 0.4,
        lambda pos: objects.Zombie(self._world, pos, self._player),
        lambda num, space: (
            0 if space < 50 else 3.5 - 3 * light, 3.5 - 3 * light))
```
1. Los zombis **solo se generan sobre material `'grass'`** (`mask = self._world.mask(*chunk, 'grass')`). Una madriguera excavada en roca tiene suelo de material `'path'`, por lo que no puede generarse un zombi en ella.
2. La condición de generación exige además distancia mínima al jugador: `away = self._player.distance(pos) >= 6`. El zombi solo puede spawnear a distancia Manhattan $\ge 6$. Estando el jugador en la madriguera, ninguna casilla interna está a distancia $\ge 6$.

Tampoco los esqueletos (`crafter/env.py:148-151`): aunque spawnean en `'path'`, exigen `distance >= 7` y al menos 6 casillas de path en el chunk (`space < 6 -> 0`).

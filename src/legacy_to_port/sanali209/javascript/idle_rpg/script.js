// --- DOM Элементы ---
const playerLevelEl = document.getElementById('player-level');
const playerHealthEl = document.getElementById('player-health');
const playerMaxHealthEl = document.getElementById('player-max-health');
const playerDamageEl = document.getElementById('player-damage');
const playerGoldEl = document.getElementById('player-gold');
const playerSteelEl = document.getElementById('player-steel');
const playerWoodEl = document.getElementById('player-wood');
const upgradeDamageBtn = document.getElementById('upgrade-damage-btn');
const upgradeDamageCostEl = document.getElementById('upgrade-damage-cost');

const enemyLevelEl = document.getElementById('enemy-level');
const enemyNameEl = document.getElementById('enemy-name');
const enemyHealthEl = document.getElementById('enemy-health');
const enemyMaxHealthEl = document.getElementById('enemy-max-health');
const enemyHealthBar = document.getElementById('enemy-health-bar');

const slotWeaponEl = document.getElementById('slot-weapon');
const slotArmorEl = document.getElementById('slot-armor');
const backpackListEl = document.getElementById('backpack-list');

const logListEl = document.getElementById('log-list');

// --- Классы ---

class Item {
    // Добавляем опциональный параметр id
    constructor(name, type, level, stats, upgradeCost, id = null) {
        // Используем предоставленный id или генерируем новый
        this.id = id !== null ? id : Date.now() + Math.random();
        this.name = name;
        this.type = type; // 'weapon', 'armor'
        this.level = level;
        this.stats = stats; // { damage: 5 } или { health: 10, defense: 2 }
        this.upgradeCost = upgradeCost; // { gold: 10, steel: 5 }
    }

    // Метод для улучшения предмета (пока не реализован)
    upgrade() {
        // Логика улучшения предмета
        console.log(`Upgrading ${this.name}...`);
    }

    getStatString() {
        let statsText = '';
        if (this.stats.damage) statsText += `Урон: +${this.stats.damage}`;
        if (this.stats.health) statsText += ` Здоровье: +${this.stats.health}`;
        if (this.stats.defense) statsText += ` Защита: +${this.stats.defense}`;
        return statsText.trim();
    }
}

class Enemy {
    constructor(level, name, maxHealth, currentHealth, goldDrop, itemDropChance) {
        this.level = level;
        this.name = name;
        this.maxHealth = maxHealth;
        this.currentHealth = currentHealth;
        this.goldDrop = goldDrop;
        this.itemDropChance = itemDropChance;
    }

    takeDamage(damage) {
        this.currentHealth -= damage;
        return this.currentHealth <= 0; // Возвращает true, если враг побежден
    }
}

class Player {
    constructor() {
        this.level = 1;
        this.baseMaxHealth = 100;
        this.currentHealth = this.baseMaxHealth;
        this.baseDamage = 1;
        this.gold = 0;
        this.steel = 0;
        this.wood = 0;
        this.equipment = {
            weapon: null,
            armor: null,
        };
        this.backpack = [];
        this.damageUpgradeCost = 10;
        this.damageUpgradeLevel = 0;
        this.maxBackpackSize = 20;
    }

    calculateMaxHealth() {
        let totalHealth = this.baseMaxHealth;
        if (this.equipment.armor && this.equipment.armor.stats.health) {
            totalHealth += this.equipment.armor.stats.health;
        }
        // TODO: Добавить бонусы от уровня игрока и т.д.
        return totalHealth;
    }

    calculateDamage() {
        let totalDamage = this.baseDamage;
        if (this.equipment.weapon && this.equipment.weapon.stats.damage) {
            totalDamage += this.equipment.weapon.stats.damage;
        }
        return totalDamage;
    }

    // Пока игрок не получает урон, но метод может пригодиться
    takeDamage(damage) {
         // TODO: Учесть защиту от брони
        this.currentHealth -= damage;
        if (this.currentHealth < 0) this.currentHealth = 0;
        // TODO: Логика смерти игрока?
    }

    heal(amount) {
        this.currentHealth += amount;
        const maxHealth = this.calculateMaxHealth();
        if (this.currentHealth > maxHealth) {
            this.currentHealth = maxHealth;
        }
    }

    canAfford(cost) {
        // Проверяет, хватает ли ресурсов для стоимости (cost = { gold: 10, steel: 5 })
        return (!cost.gold || this.gold >= cost.gold) &&
               (!cost.steel || this.steel >= cost.steel) &&
               (!cost.wood || this.wood >= cost.wood);
    }

    spendResources(cost) {
        if (this.canAfford(cost)) {
            if (cost.gold) this.gold -= cost.gold;
            if (cost.steel) this.steel -= cost.steel;
            if (cost.wood) this.wood -= cost.wood;
            return true;
        }
        return false;
    }

    addResources(rewards) {
         if (rewards.gold) this.gold += rewards.gold;
         if (rewards.steel) this.steel += rewards.steel;
         if (rewards.wood) this.wood += rewards.wood;
    }

    upgradeBaseDamage() {
        const cost = { gold: this.damageUpgradeCost };
        if (this.spendResources(cost)) {
            this.baseDamage += 1;
            this.damageUpgradeLevel++;
            this.damageUpgradeCost = Math.floor(10 * Math.pow(1.15, this.damageUpgradeLevel));
            return true; // Успешно
        }
        return false; // Не хватило золота
    }

    addItemToBackpack(item) {
        if (this.backpack.length < this.maxBackpackSize) {
            this.backpack.push(item);
            return true;
        }
        return false; // Рюкзак полон
    }

    // Принимаем ID предмета, а не индекс
    toggleEquipItemById(itemId) {
        console.log(`[Player.toggleEquipItemById] Called with ID: ${itemId}`);

        const itemIndex = this.backpack.findIndex(item => item.id === itemId);

        if (itemIndex === -1) {
            console.error(`[Player.toggleEquipItemById] Item with ID ${itemId} not found in backpack.`);
            return { success: false, message: "Предмет не найден в рюкзаке." };
        }

        const itemToEquip = this.backpack[itemIndex]; // Предмет, который хотим экипировать
        console.log("[Player.toggleEquipItemById] Found item to equip:", JSON.stringify(itemToEquip));

        const itemType = itemToEquip.type;
        const currentEquippedItem = this.equipment[itemType]; // Предмет, который сейчас надет (может быть null)
        let messages = [];

        // --- Логика обмена ---
        // 1. Удаляем предмет, который хотим экипировать, из рюкзака
        this.backpack.splice(itemIndex, 1);
        console.log(`[Player.toggleEquipItemById] Item ${itemToEquip.name} removed from backpack at index ${itemIndex}.`);

        // 2. Если был надет другой предмет этого типа, добавляем его в рюкзак
        if (currentEquippedItem) {
            // Проверка места НЕ нужна, т.к. мы только что освободили одно место
            this.backpack.push(currentEquippedItem);
            messages.push(`Предмет "${currentEquippedItem.name}" снят и помещен в рюкзак.`);
            console.log(`[Player.toggleEquipItemById] Item ${currentEquippedItem.name} added back to backpack.`);
        }

        // 3. Экипируем новый предмет
        this.equipment[itemType] = itemToEquip;
        messages.push(`Предмет "${itemToEquip.name}" экипирован.`);
        console.log(`[Player.toggleEquipItemById] Item ${itemToEquip.name} equipped in slot ${itemType}.`);
        console.log("[Player.toggleEquipItemById] Final backpack state:", JSON.stringify(this.backpack.map(i => i.name)));
        console.log("[Player.toggleEquipItemById] Final equipment state:", JSON.stringify(this.equipment));


        // 4. Обновляем характеристики игрока
        const maxHealth = this.calculateMaxHealth();
        if (this.currentHealth > maxHealth) {
            this.currentHealth = maxHealth;
        }

        console.log("[Player.toggleEquipItemById] Equip successful.");
        return { success: true, message: messages.join(' ') };
    }

     // Получение данных для сохранения
    getSaveData() {
        // Преобразуем предметы в простые объекты для JSON
        const backpackData = this.backpack.map(item => ({ ...item }));
        const equipmentData = {
            weapon: this.equipment.weapon ? { ...this.equipment.weapon } : null,
            armor: this.equipment.armor ? { ...this.equipment.armor } : null,
        };

        return {
            level: this.level,
            baseMaxHealth: this.baseMaxHealth,
            currentHealth: this.currentHealth,
            baseDamage: this.baseDamage,
            gold: this.gold,
            steel: this.steel,
            wood: this.wood,
            equipment: equipmentData,
            backpack: backpackData,
            damageUpgradeCost: this.damageUpgradeCost,
            damageUpgradeLevel: this.damageUpgradeLevel,
        };
    }

    // Загрузка данных
    loadSaveData(data) {
        this.level = data.level;
        this.baseMaxHealth = data.baseMaxHealth;
        this.currentHealth = data.currentHealth;
        this.baseDamage = data.baseDamage;
        this.gold = data.gold;
        this.steel = data.steel;
        this.wood = data.wood;
        this.damageUpgradeCost = data.damageUpgradeCost;
        this.damageUpgradeLevel = data.damageUpgradeLevel;

        // Восстанавливаем предметы, передавая сохраненный ID
        this.backpack = data.backpack.map(itemData => new Item(itemData.name, itemData.type, itemData.level, itemData.stats, itemData.upgradeCost, itemData.id)); // Передаем itemData.id
        this.equipment.weapon = data.equipment.weapon ? new Item(data.equipment.weapon.name, data.equipment.weapon.type, data.equipment.weapon.level, data.equipment.weapon.stats, data.equipment.weapon.upgradeCost, data.equipment.weapon.id) : null; // Передаем itemData.id
        this.equipment.armor = data.equipment.armor ? new Item(data.equipment.armor.name, data.equipment.armor.type, data.equipment.armor.level, data.equipment.armor.stats, data.equipment.armor.upgradeCost, data.equipment.armor.id) : null; // Передаем itemData.id

        // Убедимся, что текущее здоровье не больше максимального после загрузки
         const maxHealth = this.calculateMaxHealth();
         if (this.currentHealth > maxHealth) {
             this.currentHealth = maxHealth;
         }
    }
}

class Game {
    constructor() {
        this.player = new Player();
        this.enemy = null;
        this.currentLevel = 1;
        this.lastUpdate = Date.now();
        this.saveInterval = 30000; // 30 секунд
        this.lastSave = Date.now();
        this.logMessages = [];

        // Игровые данные (можно вынести в отдельный конфиг)
        this.enemyNames = ["Гоблин", "Скелет", "Орк", "Слизень", "Волк"];
        this.itemData = {
            weapon: [
                { name: "Ржавый меч", baseStat: 1, type: 'damage' },
                { name: "Дубинка", baseStat: 2, type: 'damage' },
                { name: "Короткий лук", baseStat: 3, type: 'damage' },
                { name: "Стальной кинжал", baseStat: 4, type: 'damage' },
            ],
            armor: [
                { name: "Кожаная куртка", baseStat: 5, type: 'health' }, // Броня дает здоровье
                { name: "Железный нагрудник", baseStat: 10, type: 'health' },
                { name: "Щит деревянный", baseStat: 3, type: 'health' }, // Можно добавить defense
            ]
        };
        this.baseUpgradeCost = { gold: 10, steel: 5 }; // Базовая стоимость улучшения предмета

        this.bindEvents();
        this.loadGame(); // Загружаем игру при инициализации
        this.startGameLoop();
    }

    addLog(message) {
        const timestamp = new Date().toLocaleTimeString();
        this.logMessages.unshift(`[${timestamp}] ${message}`); // Добавляем в начало
        if (this.logMessages.length > 50) {
            this.logMessages.pop(); // Удаляем старое сообщение
        }
        this.updateLogUI(); // Обновляем только лог
    }

    generateEnemy() {
        const level = this.currentLevel;
        const name = this.enemyNames[Math.floor(Math.random() * this.enemyNames.length)];
        const healthMultiplier = 1 + (level - 1) * 0.5;
        const goldMultiplier = 1 + (level - 1) * 0.2;
        const maxHealth = Math.floor(10 * healthMultiplier);
        const goldDrop = Math.floor(5 * goldMultiplier);
        const itemDropChance = 0.15; // Увеличим шанс дропа для теста

        this.enemy = new Enemy(level, name, maxHealth, maxHealth, goldDrop, itemDropChance);
        this.addLog(`Появляется новый враг: ${this.enemy.name} (Ур. ${this.enemy.level})`);
    }

    generateItemDrop() {
        const level = this.currentLevel;
        const itemTypeKey = Math.random() < 0.5 ? 'weapon' : 'armor';
        const possibleItems = this.itemData[itemTypeKey];
        const itemBaseData = possibleItems[Math.floor(Math.random() * possibleItems.length)];

        const name = itemBaseData.name;
        const type = itemTypeKey;
        const itemLevel = 1; // Начальный уровень предмета
        const stats = {};
        const statBoost = Math.ceil(level * (Math.random() * 0.5 + 0.5)); // Бонус зависит от уровня локации

        if (itemBaseData.type === 'damage') {
            stats.damage = itemBaseData.baseStat + statBoost;
        } else if (itemBaseData.type === 'health') {
            stats.health = itemBaseData.baseStat * 5 + statBoost * 5; // Здоровье скалируется больше
            // stats.defense = Math.floor(itemBaseData.baseStat / 2) + Math.floor(statBoost / 2); // Пример добавления защиты
        }

        // Усложним стоимость улучшения в зависимости от базовой статы
        const upgradeCost = {
             gold: Math.floor(this.baseUpgradeCost.gold * (1 + itemBaseData.baseStat * 0.2)),
             steel: Math.floor(this.baseUpgradeCost.steel * (1 + itemBaseData.baseStat * 0.1))
        };


        return new Item(name, type, itemLevel, stats, upgradeCost);
    }

    handleEnemyDefeat() {
        this.addLog(`Враг "${this.enemy.name}" (Ур. ${this.enemy.level}) побежден!`);
        const rewards = { gold: this.enemy.goldDrop };
        // TODO: Добавить выпадение стали/дерева
        this.player.addResources(rewards);
        this.addLog(`Получено ${rewards.gold} золота.`);

        // Шанс дропа предмета
        if (Math.random() < this.enemy.itemDropChance) {
            const newItem = this.generateItemDrop();
            if (this.player.addItemToBackpack(newItem)) {
                this.addLog(`Выпал предмет: ${newItem.name}!`);
            } else {
                this.addLog(`Выпал предмет: ${newItem.name}, но рюкзак полон!`);
            }
        }

        this.currentLevel++;
        this.generateEnemy(); // Генерируем нового врага
        this.saveGame(); // Сохраняем после победы
    }

    gameLoop() {
        const now = Date.now();
        const deltaTime = (now - this.lastUpdate) / 1000; // Секунды с прошлого кадра
        this.lastUpdate = now;

        if (this.enemy) {
            const damagePerSecond = this.player.calculateDamage();
            const damageDealt = damagePerSecond * deltaTime;
            const isDefeated = this.enemy.takeDamage(damageDealt);

            if (isDefeated) {
                this.handleEnemyDefeat();
            }
        } else {
            this.generateEnemy(); // Генерируем первого врага, если его нет
        }

        // Периодическое сохранение
        if (now - this.lastSave > this.saveInterval) {
            this.saveGame();
            this.lastSave = now;
        }

        this.updateUI(); // Обновляем весь UI
        requestAnimationFrame(() => this.gameLoop()); // Планируем следующий кадр
    }

    startGameLoop() {
        this.lastUpdate = Date.now(); // Сброс времени перед запуском
        requestAnimationFrame(() => this.gameLoop());
    }

    updateUI() {
        // Игрок
        playerLevelEl.textContent = this.player.level;
        playerHealthEl.textContent = Math.ceil(this.player.currentHealth);
        playerMaxHealthEl.textContent = this.player.calculateMaxHealth();
        playerDamageEl.textContent = this.player.calculateDamage();
        playerGoldEl.textContent = this.player.gold;
        playerSteelEl.textContent = this.player.steel;
        playerWoodEl.textContent = this.player.wood;
        upgradeDamageCostEl.textContent = this.player.damageUpgradeCost;
        upgradeDamageBtn.disabled = !this.player.canAfford({ gold: this.player.damageUpgradeCost });

        // Враг
        if (this.enemy) {
            enemyLevelEl.textContent = this.enemy.level;
            enemyNameEl.textContent = this.enemy.name;
            enemyHealthEl.textContent = Math.max(0, Math.ceil(this.enemy.currentHealth));
            enemyMaxHealthEl.textContent = this.enemy.maxHealth;
            const healthPercentage = Math.max(0, (this.enemy.currentHealth / this.enemy.maxHealth) * 100);
            enemyHealthBar.style.width = `${healthPercentage}%`;
        } else {
            enemyLevelEl.textContent = "-";
            enemyNameEl.textContent = "-";
            enemyHealthEl.textContent = "-";
            enemyMaxHealthEl.textContent = "-";
            enemyHealthBar.style.width = `0%`;
        }

        // Инвентарь - Экипировка
        const weapon = this.player.equipment.weapon;
        const armor = this.player.equipment.armor;
        slotWeaponEl.textContent = weapon ? `${weapon.name} (${weapon.getStatString()})` : "Пусто";
        slotArmorEl.textContent = armor ? `${armor.name} (${armor.getStatString()})` : "Пусто";

        // Инвентарь - Рюкзак
        this.updateBackpackUI();
        // Лог обновляется отдельно в addLog
    }

    updateBackpackUI() {
        backpackListEl.innerHTML = ''; // Очищаем список
        if (this.player.backpack.length === 0) {
            const li = document.createElement('li');
            li.textContent = "Пусто";
            backpackListEl.appendChild(li);
        } else {
            this.player.backpack.forEach((item, index) => {
                const li = document.createElement('li');
                li.textContent = `${item.name} (Ур. ${item.level}) [${item.getStatString()}]`;
                li.classList.add('item');
                li.dataset.itemId = item.id;
                li.dataset.itemIndex = index;
                li.title = "Кликните, чтобы экипировать/снять";
                backpackListEl.appendChild(li);
            });
        }
    }

     updateLogUI() {
        logListEl.innerHTML = ''; // Очищаем лог
        this.logMessages.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = msg;
            logListEl.appendChild(li); // Добавляем в конец (т.к. новые в начало массива)
        });
    }

    bindEvents() {
        upgradeDamageBtn.addEventListener('click', () => {
            if (this.player.upgradeBaseDamage()) {
                this.addLog(`Урон улучшен! Новый базовый урон: ${this.player.baseDamage}.`);
                this.updateUI(); // Обновляем UI для отображения новой стоимости
                this.saveGame();
            } else {
                this.addLog("Недостаточно золота для улучшения урона.");
            }
        });

        backpackListEl.addEventListener('click', (event) => {
            const target = event.target.closest('li.item');
            if (target) {
                const itemIndex = parseInt(target.dataset.itemIndex, 10); // Все еще получаем индекс для логов
                const itemId = parseFloat(target.dataset.itemId);
                console.log(`[Game.bindEvents] Click detected on index: ${itemIndex}, ID: ${itemId}`);

                if (!isNaN(itemId)) {
                    // Теперь вызываем метод по ID
                    console.log(`[Game.bindEvents] Calling toggleEquipItemById with ID: ${itemId}`);
                    const result = this.player.toggleEquipItemById(itemId);
                    this.addLog(result.message);
                    if (result.success) {
                        console.log("[Game.bindEvents] Equip successful, updating UI and saving.");
                        this.updateUI();
                        this.saveGame();
                    } else {
                         console.warn("[Game.bindEvents] Equip failed:", result.message);
                         // Можно добавить обновление UI здесь, если ошибка могла вызвать рассинхрон
                         this.updateUI();
                    }
                } else {
                    console.error("[Game.bindEvents] Could not parse item ID from dataset:", target.dataset);
                }
            }
        });
    }

    saveGame() {
        const saveData = {
            player: this.player.getSaveData(),
            currentLevel: this.currentLevel,
            // Сохраняем врага, чтобы продолжить бой с тем же здоровьем
            enemy: this.enemy ? {
                 level: this.enemy.level,
                 name: this.enemy.name,
                 maxHealth: this.enemy.maxHealth,
                 currentHealth: this.enemy.currentHealth,
                 goldDrop: this.enemy.goldDrop,
                 itemDropChance: this.enemy.itemDropChance
            } : null,
            logMessages: this.logMessages // Сохраняем лог
        };
        try {
            localStorage.setItem('idleRpgGameStateOOP', JSON.stringify(saveData));
            // console.log("Game saved (OOP)");
        } catch (error) {
            console.error("Ошибка сохранения игры (OOP):", error);
            this.addLog("Ошибка при сохранении игры!");
        }
    }

    loadGame() {
        const savedDataString = localStorage.getItem('idleRpgGameStateOOP');
        if (savedDataString) {
            try {
                const loadedData = JSON.parse(savedDataString);
                if (loadedData && loadedData.player && loadedData.currentLevel) {
                    this.player.loadSaveData(loadedData.player);
                    this.currentLevel = loadedData.currentLevel;
                    this.logMessages = loadedData.logMessages || []; // Загружаем лог

                    // Восстанавливаем врага
                    if (loadedData.enemy) {
                        const ed = loadedData.enemy;
                        this.enemy = new Enemy(ed.level, ed.name, ed.maxHealth, ed.currentHealth, ed.goldDrop, ed.itemDropChance);
                    } else {
                        this.enemy = null; // Или генерируем нового? Пока null
                    }

                    this.addLog("Сохраненная игра (OOP) загружена.");
                } else {
                     this.addLog("Некорректные сохраненные данные (OOP). Начинаем новую игру.");
                     this.initializeNewGame();
                }
            } catch (error) {
                console.error("Ошибка загрузки игры (OOP):", error);
                this.addLog("Ошибка при загрузке сохраненной игры (OOP). Начинаем новую игру.");
                localStorage.removeItem('idleRpgGameStateOOP');
                this.initializeNewGame();
            }
        } else {
            this.addLog("Сохраненная игра (OOP) не найдена. Начинаем новую игру.");
            this.initializeNewGame();
        }
        // Обновляем UI после загрузки или инициализации
        this.updateUI();
        this.updateLogUI(); // Обновляем лог отдельно
    }

    initializeNewGame() {
        this.player = new Player(); // Создаем нового игрока
        this.enemy = null;
        this.currentLevel = 1;
        this.logMessages = []; // Очищаем лог
        this.generateEnemy(); // Генерируем первого врага
        this.addLog("Начинается новая игра!");
        // UI обновится в loadGame или при первом вызове gameLoop
    }
}

// --- Запуск игры ---
const game = new Game();

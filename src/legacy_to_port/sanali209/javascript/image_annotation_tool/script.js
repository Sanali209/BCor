document.addEventListener('DOMContentLoaded', () => {
    const imageFolderInput = document.getElementById('imageFolderInput');
    const appDiv = document.getElementById('app');
    const currentImage = document.getElementById('current-image');
    const imageNameP = document.getElementById('image-name');
    const prevButton = document.getElementById('prev-button');
    const nextButton = document.getElementById('next-button');
    const annotationOptions = document.querySelectorAll('input[name="annotation"]');
    const saveButton = document.getElementById('save-button');
    const loadJsonInput = document.getElementById('load-json-input');

    let imageFiles = [];
    let annotations = {}; // { 'imageName.jpg': 'normal', ... }
    let currentIndex = -1;

    // --- Обработка выбора папки ---
    imageFolderInput.addEventListener('change', (event) => {
        const files = event.target.files;
        if (!files.length) {
            alert('Папка не выбрана или пуста.');
            return;
        }

        // Фильтруем только файлы изображений (простая проверка по расширению)
        imageFiles = Array.from(files).filter(file =>
            /\.(jpe?g|png|gif|bmp|webp)$/i.test(file.name)
        );

        if (!imageFiles.length) {
            alert('В выбранной папке нет поддерживаемых изображений (jpg, png, gif, bmp, webp).');
            appDiv.style.display = 'none'; // Скрываем интерфейс, если нет изображений
            return;
        }

        console.log(`Найдено изображений: ${imageFiles.length}`);
        annotations = {}; // Сбрасываем аннотации при выборе новой папки
        currentIndex = 0;
        displayImage(currentIndex);
        appDiv.style.display = 'flex'; // Показываем основной интерфейс
    });

    // --- Отображение изображения и аннотации ---
    function displayImage(index) {
        if (index < 0 || index >= imageFiles.length) {
            console.error("Неверный индекс изображения:", index);
            return;
        }
        const file = imageFiles[index];
        const reader = new FileReader();

        reader.onload = (e) => {
            currentImage.src = e.target.result;
        }
        reader.readAsDataURL(file); // Читаем файл как Data URL

        imageNameP.textContent = file.name;
        currentIndex = index;

        // Обновляем состояние кнопок навигации
        prevButton.disabled = index === 0;
        nextButton.disabled = index === imageFiles.length - 1;

        // Устанавливаем сохраненную аннотацию или значение по умолчанию ('normal')
        const currentAnnotation = annotations[file.name] || 'normal';
        document.querySelector(`input[name="annotation"][value="${currentAnnotation}"]`).checked = true;
    }

    // --- Навигация ---
    prevButton.addEventListener('click', () => {
        if (currentIndex > 0) {
            saveCurrentAnnotation(); // Сохраняем аннотацию перед переходом
            displayImage(currentIndex - 1);
        }
    });

    nextButton.addEventListener('click', () => {
        if (currentIndex < imageFiles.length - 1) {
            saveCurrentAnnotation(); // Сохраняем аннотацию перед переходом
            displayImage(currentIndex + 1);
        }
    });

    // --- Обработка выбора аннотации ---
    annotationOptions.forEach(radio => {
        radio.addEventListener('change', saveCurrentAnnotation);
    });

    function saveCurrentAnnotation() {
        if (currentIndex >= 0 && currentIndex < imageFiles.length) {
            const selectedValue = document.querySelector('input[name="annotation"]:checked').value;
            const fileName = imageFiles[currentIndex].name;
            annotations[fileName] = selectedValue;
            console.log(`Аннотация для ${fileName}: ${selectedValue}`);
        }
    }

    // --- Сохранение аннотаций в JSON ---
    saveButton.addEventListener('click', () => {
        if (Object.keys(annotations).length === 0) {
            alert('Нет аннотаций для сохранения.');
            return;
        }
        saveCurrentAnnotation(); // Убедимся, что последняя аннотация сохранена

        const jsonString = JSON.stringify(annotations, null, 2); // Форматированный JSON
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'annotations.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        console.log('Аннотации сохранены в annotations.json');
    });

    // --- Загрузка аннотаций из JSON ---
    loadJsonInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const loadedAnnotations = JSON.parse(e.target.result);
                // Простая проверка, что это объект
                if (typeof loadedAnnotations === 'object' && loadedAnnotations !== null) {
                    annotations = loadedAnnotations;
                    console.log('Аннотации загружены:', annotations);
                    // Обновляем аннотацию для текущего изображения, если оно есть в загруженном файле
                    if (currentIndex >= 0 && currentIndex < imageFiles.length) {
                         const currentFileName = imageFiles[currentIndex].name;
                         const currentAnnotation = annotations[currentFileName] || 'normal';
                         document.querySelector(`input[name="annotation"][value="${currentAnnotation}"]`).checked = true;
                    }
                     alert('Аннотации успешно загружены!');
                } else {
                    throw new Error('Некорректный формат JSON.');
                }
            } catch (error) {
                console.error('Ошибка при загрузке или парсинге JSON:', error);
                alert(`Ошибка загрузки файла: ${error.message}`);
            } finally {
                 // Сбрасываем значение input, чтобы можно было загрузить тот же файл снова
                 loadJsonInput.value = '';
            }
        };
        reader.onerror = () => {
            console.error('Ошибка чтения файла.');
            alert('Не удалось прочитать файл.');
            loadJsonInput.value = '';
        };
        reader.readAsText(file);
    });

});

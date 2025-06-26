// client/postcss.config.js          <-- перезаписываем целиком
import tailwind from '@tailwindcss/postcss';
import autoprefixer from 'autoprefixer';

export default {
  plugins: [
    // плагин Tailwind CSS v4
    tailwind({
      // если конфиг лежит НЕ рядом с этим файлом, укажите относительный путь
      config: './tailwind.config.js',
    }),
    // автопрефиксер
    autoprefixer,
  ],
};
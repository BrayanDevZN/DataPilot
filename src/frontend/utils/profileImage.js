const MAX_FILE_SIZE = 5 * 1024 * 1024;
const OUTPUT_SIZE = 480;

export function fileToProfileImage(file) {
  if (!file) {
    return Promise.reject(new Error("Selecione uma imagem."));
  }

  if (!file.type.startsWith("image/")) {
    return Promise.reject(new Error("Selecione um arquivo de imagem válido."));
  }

  if (file.size > MAX_FILE_SIZE) {
    return Promise.reject(new Error("A imagem deve ter no máximo 5 MB."));
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onerror = () => reject(new Error("Não foi possível ler a imagem."));

    reader.onload = () => {
      const image = new Image();

      image.onerror = () => reject(new Error("Não foi possível processar a imagem."));

      image.onload = () => {
        const sourceSize = Math.min(image.width, image.height);
        const sourceX = (image.width - sourceSize) / 2;
        const sourceY = (image.height - sourceSize) / 2;
        const canvas = document.createElement("canvas");

        canvas.width = OUTPUT_SIZE;
        canvas.height = OUTPUT_SIZE;

        const context = canvas.getContext("2d");

        context.drawImage(
          image,
          sourceX,
          sourceY,
          sourceSize,
          sourceSize,
          0,
          0,
          OUTPUT_SIZE,
          OUTPUT_SIZE
        );

        resolve(canvas.toDataURL("image/jpeg", 0.84));
      };

      image.src = reader.result;
    };

    reader.readAsDataURL(file);
  });
}

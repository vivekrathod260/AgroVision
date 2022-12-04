MODEL_PATH = str(os.getcwd())+'/Home/Model/Model1.h5'
model = load_model(MODEL_PATH)

CLASS_NAMES = ["Early Blight", "Late Blight", "Healthy"]

image = np.array(Image.open(str(os.getcwd())+"/static/uploads/"+imgName))

img_batch = np.expand_dims(image, 0)

predictions = model.predict(img_batch)

predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
confidence = np.max(predictions[0])
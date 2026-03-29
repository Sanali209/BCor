from gradio_client import Client, file

client = Client("visheratin/mc-llava-3b")
result = client.predict(
		file("37019507112_f2d61af76a_b.jpg"),	# filepath  in 'Upload or Drag an Image' Image component
		"what on image?",	# str  in 'Question' Textbox component
		0,	# float (numeric value between 0 and 200) in 'Max crops' Slider component
		728,	# float (numeric value between 728 and 2184) in 'Number of image tokens' Slider component
		False,	# bool  in 'Sample' Checkbox component
		0,	# float (numeric value between 0 and 1) in 'Temperature' Slider component
		0,	# float (numeric value between 0 and 50) in 'Top-K' Slider component
		api_name="/answer_question"
)
print(result)
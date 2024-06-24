import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from time import gmtime, strftime, time
from decimal import Decimal, getcontext

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rpi_Track')
client = boto3.client('iot-data', region_name='XYZ')
topic = 'rpi_Car/control'

def mqttPub(speed, direction, wheelAngle, time_difference):    
	# publish to Mqtt stream 
	payload = json.dumps({'Speed': speed, 'Direction': direction, 'Wheel Angle': wheelAngle, 'timeDifference': str(time_difference)})
	response = client.publish(
		topic=topic,
		qos=1, 
		payload=payload
	)

def lambda_handler(event, context):
	try:
		if 'send_trackId' not in event:
			trackId = int(event.get('trackId'))
			speed = event.get('speed')
			direction = event.get('direction')
			wheelAngle = event.get('wheelAngle')
			
			mqttPub(speed, direction, wheelAngle, 0)
			
			if trackId > 0 and trackId <= 10:
				# write to database 
				now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
				
				response = table.put_item(
					Item={
						'InstructionID': now,
						'TrackID': str(trackId),
						'Speed': speed,
						'Direction': direction,
						'Wheel Angle': wheelAngle,
					}   
				)
				
				return {
					'statusCode': 200,
					'body': json.dumps('Complete instructions ')
				}
			else:
				return {'statusCode': 400, 'body': 'Invalid trackId'}
		elif 'send_trackId' in event:
			
			trackid = str(event.get('send_trackId'))
			filter_expression = 'TrackID = :tid'
			expression_attribute_values = {':tid': trackid}

			# Fetch trackId values from the database
			response = table.scan(FilterExpression=filter_expression, ExpressionAttributeValues=expression_attribute_values)
			if 'Items' in response:
				items = response['Items']
				items = sorted(items, key=lambda x: x['InstructionID'])
				for index, item in enumerate(items):
					trackId = int(item.get('TrackID'))
					speed = item.get('Speed')
					direction = item.get('Direction')
					wheelAngle = item.get('Wheel Angle')
					time_difference = item.get('InstructionID')
					mqttPub(speed, direction, wheelAngle, time_difference)
					
					
				return {'statusCode': 200, 'body': json.dumps('Complete instructions ')}
			else:
				print("No items found.")
	except Exception as e:
		print('Error processing instructions:', str(e))

const AWS = require('aws-sdk');

const s3 = new AWS.S3({ signatureVersion: 'v4' });
const dynamodb = new AWS.DynamoDB.DocumentClient();

const PHOTO_BUCKET = process.env.PHOTO_BUCKET;
const PHOTOS_TABLE = process.env.PHOTOS_TABLE;

exports.handler = async (event) => {
  try {
    const photoId = event.pathParameters?.photoId;
    const userId = event.queryStringParameters?.userId;

    if (!userId || !photoId) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'userId query param and photoId path param are required' })
      };
    }

    const item = await dynamodb.get({
      TableName: PHOTOS_TABLE,
      Key: {
        UserId: userId,
        PhotoId: photoId
      }
    }).promise();

    if (!item.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({ error: 'photo not found' })
      };
    }

    const downloadUrl = await s3.getSignedUrlPromise('getObject', {
      Bucket: PHOTO_BUCKET,
      Key: item.Item.ObjectKey,
      Expires: 3600
    });

    return {
      statusCode: 200,
      body: JSON.stringify({
        downloadUrl,
        expiresInSeconds: 3600
      })
    };
  } catch (error) {
    console.error('download handler error', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'internal server error' })
    };
  }
};

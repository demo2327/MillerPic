const AWS = require('aws-sdk');

const s3 = new AWS.S3({ signatureVersion: 'v4' });
const dynamodb = new AWS.DynamoDB.DocumentClient();

const PHOTO_BUCKET = process.env.PHOTO_BUCKET;
const PHOTOS_TABLE = process.env.PHOTOS_TABLE;

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body || '{}');
    const userId = body.userId;
    const photoId = body.photoId;
    const contentType = body.contentType || 'image/webp';

    if (!userId || !photoId) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'userId and photoId are required' })
      };
    }

    const objectKey = `originals/${userId}/${photoId}.webp`;

    await dynamodb.put({
      TableName: PHOTOS_TABLE,
      Item: {
        UserId: userId,
        PhotoId: photoId,
        ObjectKey: objectKey,
        ContentType: contentType,
        CreatedAt: new Date().toISOString()
      }
    }).promise();

    const uploadUrl = await s3.getSignedUrlPromise('putObject', {
      Bucket: PHOTO_BUCKET,
      Key: objectKey,
      ContentType: contentType,
      Expires: 900
    });

    return {
      statusCode: 200,
      body: JSON.stringify({
        uploadUrl,
        objectKey,
        expiresInSeconds: 900
      })
    };
  } catch (error) {
    console.error('upload handler error', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'internal server error' })
    };
  }
};

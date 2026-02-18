# Desktop Verification Checklist

## Session Info
- Date: 2026-02-18
- Tester: WhyNoDad
- Windows version: Windows 11 Home 25H2 (OS build 26200.7840)
- App launch method (terminal/shortcut): VS Code Terminal -> Run Task -> Desktop: Run App
- Network context (VPN/proxy on/off): No VPN/proxy; Starlink internet via TP-Link mesh Wi-Fi

## Test Data Used
- Small image file:
- Large image/video file:
- Download target folder:

## Execution Checklist
Mark each item as you go.

Scope note: steps 9-11 are currently API-capability checks and may not be visible in the desktop UI yet.

- [x] 1) Launch app from `desktop-client/app.py` (no crash on startup)
used the VS code Terminal>Run Task>Desktop: Run App
- [x] 2) Google sign-in completes (no auth loop/error dialog)
- [x] 3) Initial photo list loads (or empty-state renders correctly)
- [x] 4) Upload one small image (`.jpg`/`.png`) succeeds
Web capture_7-11-2021_18379_myaccount.gflenv.com.jpeg   219 KB
cannot see file in the list, don't know how to go to next page when set to 20, and when I set it to 100 I first only got 9 files in the list, then 67 but the file uploaded did not show
- [x] 5) Upload one larger file succeeds
20220723_121102.jpg  30341 KB
same result cannot see file in list
- [ ] 6) Refresh/reopen app and uploaded items persist
after closing and reopening app, I saw the large file on first list lookup, but not after changing the limit to 100, now only 48 images listed
ouptut:
Desktop client ready.
Sign in with Google or paste your Google ID token, then start with Upload Photo.
Starting Google sign-in flow in browser...
Google sign-in complete. Token field updated.
Requesting photo list...
GET /photos -> 200
{
  "photos": [
    {
      "photoId": "photo-manual-001",
      "fileName": "photo-manual-001.webp",
      "objectKey": "originals/110732209307403665878/photo-manual-001.webp",
      "contentType": "image/webp",
      "createdAt": "2026-02-16T04:15:27.902169+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "fd617c17952c429782334c120ebe2eaf",
      "fileName": "20220221_144117.jpg",
      "objectKey": "originals/110732209307403665878/fd617c17952c429782334c120ebe2eaf.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:19.495183+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "fbf3acef9b4f41e6908f7fbf41eab5b2",
      "fileName": "20220221_084148.mp4",
      "objectKey": "originals/110732209307403665878/fbf3acef9b4f41e6908f7fbf41eab5b2.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:49:48.980842+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "fa0942969e0b45e6a7a568e6c6fca00f",
      "fileName": "20220221_084148.mp4",
      "objectKey": "originals/110732209307403665878/fa0942969e0b45e6a7a568e6c6fca00f.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:57:13.368113+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "f552c607fde14148be8ec97bbda21460",
      "fileName": "20220221_081325.jpg",
      "objectKey": "originals/110732209307403665878/f552c607fde14148be8ec97bbda21460.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:56:52.456487+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "eef6a0507f854bc2b6e0219330b6f61a",
      "fileName": "20220221_101715.jpg",
      "objectKey": "originals/110732209307403665878/eef6a0507f854bc2b6e0219330b6f61a.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:18.624697+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "ebe50a1db3c94a288ef3245dd84f668f",
      "fileName": "20220221_053646.jpg",
      "objectKey": "originals/110732209307403665878/ebe50a1db3c94a288ef3245dd84f668f.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:16.039821+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "e39ddc8690774238a6b79959cb852def",
      "fileName": "20220221_101701.jpg",
      "objectKey": "originals/110732209307403665878/e39ddc8690774238a6b79959cb852def.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:07.154799+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "debbd1adb119485c89fdb7c1d71f096c",
      "fileName": "20220221_124313.jpg",
      "objectKey": "originals/110732209307403665878/debbd1adb119485c89fdb7c1d71f096c.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:37.631997+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "c91790d0f6e44bd8865652733eeaa45a",
      "fileName": "20220221_152614.jpg",
      "objectKey": "originals/110732209307403665878/c91790d0f6e44bd8865652733eeaa45a.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:58.759318+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "c8c5fdd89f544c03b3e9dd6e4ef70113",
      "fileName": "20220221_124319.jpg",
      "objectKey": "originals/110732209307403665878/c8c5fdd89f544c03b3e9dd6e4ef70113.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:48.992345+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "c3c2358d2a354640bd2a20b4b4ea3d50",
      "fileName": "20220221_152559.jpg",
      "objectKey": "originals/110732209307403665878/c3c2358d2a354640bd2a20b4b4ea3d50.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:49.768960+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "bd29f8fe33944310a2fcb323108f6d17",
      "fileName": "20220221_053652.jpg",
      "objectKey": "originals/110732209307403665878/bd29f8fe33944310a2fcb323108f6d17.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:21.770736+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "b74975a68f0b48d2aa5b8dc774eda256",
      "fileName": "20220221_092647.mp4",
      "objectKey": "originals/110732209307403665878/b74975a68f0b48d2aa5b8dc774eda256.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:50:07.389189+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "b68f316af2fa49f28400d5c0478d3fab",
      "fileName": "20220221_101637.jpg",
      "objectKey": "originals/110732209307403665878/b68f316af2fa49f28400d5c0478d3fab.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:03.945327+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "b641cde815b9478fadfa6a381097dffa",
      "fileName": "20220221_124726.jpg",
      "objectKey": "originals/110732209307403665878/b641cde815b9478fadfa6a381097dffa.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:58.937243+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "b3b0ce13808c4e1b905b1f4a2d6d3ae8",
      "fileName": "20220221_081329.jpg",
      "objectKey": "originals/110732209307403665878/b3b0ce13808c4e1b905b1f4a2d6d3ae8.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:56:53.307940+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "b141550c78df413bb204adaf762e0d70",
      "fileName": "20220221_144116.jpg",
      "objectKey": "originals/110732209307403665878/b141550c78df413bb204adaf762e0d70.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:15.890408+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "ae6305f575bc436c9df3e46e7795cdd8",
      "fileName": "20220723_121102.jpg",
      "objectKey": "originals/110732209307403665878/ae6305f575bc436c9df3e46e7795cdd8.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-18T16:04:27.950149+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "a39f7cf22a7d46d88ca557a3399d3a86",
      "fileName": "20220221_084152.jpg",
      "objectKey": "originals/110732209307403665878/a39f7cf22a7d46d88ca557a3399d3a86.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:51.452349+00:00",
      "status": "ACTIVE"
    }
  ],
  "count": 20,
  "nextToken": "eyJVc2VySWQiOiAiMTEwNzMyMjA5MzA3NDAzNjY1ODc4IiwgIlBob3RvSWQiOiAiYTM5ZjdjZjIyYTdkNDZkODhjYTU1N2EzMzk5ZDNhODYifQ=="
}
Auto-selected first photoId for download lookup: photo-manual-001
Requesting photo list...
GET /photos -> 200
{
  "photos": [
    {
      "photoId": "a2362e11e1654e5d94d67ed42753673f",
      "fileName": "a2362e11e1654e5d94d67ed42753673f.webp",
      "objectKey": "originals/110732209307403665878/a2362e11e1654e5d94d67ed42753673f.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T04:51:39.902530+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "9961e7290f2f4882b6b39d1e0f77c56e",
      "fileName": "20220221_101554.jpg",
      "objectKey": "originals/110732209307403665878/9961e7290f2f4882b6b39d1e0f77c56e.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:53.279309+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "8e7151dac1ba4e0da8cee2f81d7aea47",
      "fileName": "20220221_101615.jpg",
      "objectKey": "originals/110732209307403665878/8e7151dac1ba4e0da8cee2f81d7aea47.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:56.427465+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "8c8b9e88818b4433b91f2eee65f1c1b2",
      "fileName": "20220221_081325.jpg",
      "objectKey": "originals/110732209307403665878/8c8b9e88818b4433b91f2eee65f1c1b2.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:25.138847+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "8c4676cdfdf0496bbb8c7ce6c17765d8",
      "fileName": "20220221_101154.jpg",
      "objectKey": "originals/110732209307403665878/8c4676cdfdf0496bbb8c7ce6c17765d8.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:27.645363+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "8c0bcdf2929a4d2296dba4e07b7eb676",
      "fileName": "20220221_101151.jpg",
      "objectKey": "originals/110732209307403665878/8c0bcdf2929a4d2296dba4e07b7eb676.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:20.780235+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "8acb57d5df0140d19d66f9884e698618",
      "fileName": "20220221_124310.jpg",
      "objectKey": "originals/110732209307403665878/8acb57d5df0140d19d66f9884e698618.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:29.783972+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "888875a769e7402482b22c8a0938fb2d",
      "fileName": "20220221_081330.jpg",
      "objectKey": "originals/110732209307403665878/888875a769e7402482b22c8a0938fb2d.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:56:55.385690+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "86b4c832a77d4af9b6f46db34868d4f4",
      "fileName": "20220221_081338.mp4",
      "objectKey": "originals/110732209307403665878/86b4c832a77d4af9b6f46db34868d4f4.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:56:56.060957+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "83c93e564c5f49628673bb710854a02c",
      "fileName": "20220221_081338.mp4",
      "objectKey": "originals/110732209307403665878/83c93e564c5f49628673bb710854a02c.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:49:29.554958+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "7cd7927aaebf4775b85a879def5e3b1e",
      "fileName": "20220221_084152.jpg",
      "objectKey": "originals/110732209307403665878/7cd7927aaebf4775b85a879def5e3b1e.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:57:15.814998+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "7b2fc5ef59054222b1fa09540c285af4",
      "fileName": "20220221_081329.jpg",
      "objectKey": "originals/110732209307403665878/7b2fc5ef59054222b1fa09540c285af4.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:26.423396+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "6fd47364cfbb4ff4ba1fe6274d099b96",
      "fileName": "20220221_101826.jpg",
      "objectKey": "originals/110732209307403665878/6fd47364cfbb4ff4ba1fe6274d099b96.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:31.603963+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "6ed978793c0d47339ef5a5d3d371d0c7",
      "fileName": "6ed978793c0d47339ef5a5d3d371d0c7.webp",
      "objectKey": "originals/110732209307403665878/6ed978793c0d47339ef5a5d3d371d0c7.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T04:39:37.965645+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "6e6051b2f8d84598acee5b9d4d479728",
      "fileName": "20220221_124312.jpg",
      "objectKey": "originals/110732209307403665878/6e6051b2f8d84598acee5b9d4d479728.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:33.881145+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "6acff99e456140bfbb3756639a4f6e27",
      "fileName": "20180217_164424.jpg",
      "objectKey": "originals/110732209307403665878/6acff99e456140bfbb3756639a4f6e27.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T05:14:39.464785+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "60435dbaa945412695a9d7199dc60ceb",
      "fileName": "20220221_144122.mp4",
      "objectKey": "originals/110732209307403665878/60435dbaa945412695a9d7199dc60ceb.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:53:22.988383+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "5e98f2327b564dae99670fa3f5cfb46f",
      "fileName": "20220221_081330.jpg",
      "objectKey": "originals/110732209307403665878/5e98f2327b564dae99670fa3f5cfb46f.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:28.465635+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "5c9a9a92e05f49c69fa82945de62c7f6",
      "fileName": "20220221_124727.jpg",
      "objectKey": "originals/110732209307403665878/5c9a9a92e05f49c69fa82945de62c7f6.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:04.256015+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "593a8e86e09d4cf4b4e25e5bce797c26",
      "fileName": "20220221_084153.jpg",
      "objectKey": "originals/110732209307403665878/593a8e86e09d4cf4b4e25e5bce797c26.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:54.905759+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "501b5c3278d54d798d2c76b707a1a720",
      "fileName": "20220221_081353.mp4",
      "objectKey": "originals/110732209307403665878/501b5c3278d54d798d2c76b707a1a720.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:56:58.344777+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "46d962a42bc94f61992432f28f3d5a2b",
      "fileName": "20220221_101159.jpg",
      "objectKey": "originals/110732209307403665878/46d962a42bc94f61992432f28f3d5a2b.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:47.509223+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "45b9bcd080c844c0ba8ae07148318dbe",
      "fileName": "20220221_101823.jpg",
      "objectKey": "originals/110732209307403665878/45b9bcd080c844c0ba8ae07148318dbe.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:27.496198+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "435a329f4e0c467981d20d66066f2047",
      "fileName": "20220221_053652.jpg",
      "objectKey": "originals/110732209307403665878/435a329f4e0c467981d20d66066f2047.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:56:49.356020+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "4286e782218d4509b6770a989036a6ed",
      "fileName": "20220221_101731.jpg",
      "objectKey": "originals/110732209307403665878/4286e782218d4509b6770a989036a6ed.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:23.089389+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "3fff654ad97b433e8f85e859bd8f9f83",
      "fileName": "20220221_152607.jpg",
      "objectKey": "originals/110732209307403665878/3fff654ad97b433e8f85e859bd8f9f83.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:53.445570+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "3e6c9172e1964ce8b79410389795b638",
      "fileName": "20220221_101144.jpg",
      "objectKey": "originals/110732209307403665878/3e6c9172e1964ce8b79410389795b638.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:13.609066+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "3ace423f77854078b5e16a650ceba377",
      "fileName": "20220221_101157.jpg",
      "objectKey": "originals/110732209307403665878/3ace423f77854078b5e16a650ceba377.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:41.126745+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "2bb0b5d2bbb842ba97dde227d16b1429",
      "fileName": "20220221_144114.jpg",
      "objectKey": "originals/110732209307403665878/2bb0b5d2bbb842ba97dde227d16b1429.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:12.531189+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "29c04f834ede4148bd1644ec2cbb2b27",
      "fileName": "20220221_101829.jpg",
      "objectKey": "originals/110732209307403665878/29c04f834ede4148bd1644ec2cbb2b27.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:35.986460+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "29604fe6178347f3b66810e1eaff7156",
      "fileName": "20220221_053648.jpg",
      "objectKey": "originals/110732209307403665878/29604fe6178347f3b66810e1eaff7156.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:16.018413+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "264a75532db34e3ebda0ba278ac0f33b",
      "fileName": "20220221_101620.jpg",
      "objectKey": "originals/110732209307403665878/264a75532db34e3ebda0ba278ac0f33b.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:00.322808+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "26371fec8ae6425fb312a6c94756f501",
      "fileName": "20220221_081353.mp4",
      "objectKey": "originals/110732209307403665878/26371fec8ae6425fb312a6c94756f501.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:49:31.336939+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "260cf891196e445fb1f95bf6ecb87938",
      "fileName": "20220221_122547.mp4",
      "objectKey": "originals/110732209307403665878/260cf891196e445fb1f95bf6ecb87938.webp",
      "contentType": "video/mp4",
      "createdAt": "2026-02-16T20:51:40.694321+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "25e5faa8a10944dea5f0a75062be5ab1",
      "fileName": "20220221_124314.jpg",
      "objectKey": "originals/110732209307403665878/25e5faa8a10944dea5f0a75062be5ab1.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:41.279832+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "227f2b150535411fac206fd38c2504e4",
      "fileName": "20220221_084154.jpg",
      "objectKey": "originals/110732209307403665878/227f2b150535411fac206fd38c2504e4.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:03.165957+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "20933d9b6a2d4504bac4f3cab3ed608b",
      "fileName": "20220221_081324.jpg",
      "objectKey": "originals/110732209307403665878/20933d9b6a2d4504bac4f3cab3ed608b.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:21.893947+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "1f95bd24d05e4c76b3de3096cacd1e19",
      "fileName": "20220221_084154(0).jpg",
      "objectKey": "originals/110732209307403665878/1f95bd24d05e4c76b3de3096cacd1e19.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:49:59.370129+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "1f8b15a6a6ec4257b2d680d0d7639561",
      "fileName": "20220221_101156.jpg",
      "objectKey": "originals/110732209307403665878/1f8b15a6a6ec4257b2d680d0d7639561.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:50:34.523490+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "1eb921aa1a1e47379ce67df5ba7cb0ac",
      "fileName": "20220221_124726(0).jpg",
      "objectKey": "originals/110732209307403665878/1eb921aa1a1e47379ce67df5ba7cb0ac.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:53.344275+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "1645b7bd96dd4dc59e818d7b0b405f2c",
      "fileName": "20220221_081324.jpg",
      "objectKey": "originals/110732209307403665878/1645b7bd96dd4dc59e818d7b0b405f2c.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:56:49.650695+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "13be431f9fcd4ac38d0d4edbc8c4965e",
      "fileName": "20220221_101703.jpg",
      "objectKey": "originals/110732209307403665878/13be431f9fcd4ac38d0d4edbc8c4965e.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:10.917273+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "0b686577975b4247bfc871c2321c2005",
      "fileName": "IMAG0077.jpg",
      "objectKey": "originals/110732209307403665878/0b686577975b4247bfc871c2321c2005.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:18:06.642075+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "0b28d76c10e54661b1cbe944bcd01890",
      "fileName": "20220221_144111.jpg",
      "objectKey": "originals/110732209307403665878/0b28d76c10e54661b1cbe944bcd01890.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:53:09.416561+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "0580b24b08e14be9af1baa5a1c94d095",
      "fileName": "20220221_053648.jpg",
      "objectKey": "originals/110732209307403665878/0580b24b08e14be9af1baa5a1c94d095.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:56:44.760104+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "0494431ac5ee4444801987912fa8bc2d",
      "fileName": "20220221_053646.jpg",
      "objectKey": "originals/110732209307403665878/0494431ac5ee4444801987912fa8bc2d.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:56:44.777696+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "035ebc5f2130464e912fa852906cf6c6",
      "fileName": "20220221_124318.jpg",
      "objectKey": "originals/110732209307403665878/035ebc5f2130464e912fa852906cf6c6.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:52:44.489391+00:00",
      "status": "ACTIVE"
    },
    {
      "photoId": "012e655f1a4b4955b8822ca4b2168d60",
      "fileName": "20220221_101709.jpg",
      "objectKey": "originals/110732209307403665878/012e655f1a4b4955b8822ca4b2168d60.webp",
      "contentType": "image/jpeg",
      "createdAt": "2026-02-16T20:51:14.574052+00:00",
      "status": "ACTIVE"
    }
  ],
  "count": 48,
  "nextToken": null
}
Auto-selected first photoId for download lookup: a2362e11e1654e5d94d67ed42753673f


- [x] 7) Open/download a photo and verify output file is valid
I was able to open 2 image files
ouptut:
Requesting download URL for selected photoId=6acff99e456140bfbb3756639a4f6e27...
GET /photos/{photoId}/download-url -> 200
{
  "downloadUrl": "https://millerpic-photos-dev.s3.amazonaws.com/originals/110732209307403665878/6acff99e456140bfbb3756639a4f6e27.webp?AWSAccessKeyId=ASIA5PLWJANYF3EEN2J5&Signature=m3XI1wk0H24lGE8HjwOBru52VXg%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEKH%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIBStZvg%2FutjAo4Q7Y%2BL2%2Fp55Vm7zU8I5EAySQ4eoavi3AiEA1luZVxGFh0LC6KdjIl2uDxO%2BM5MQwW8m654SkB5zjYoqgAMIaRAEGgw5MjYzNTAzNzc4NDAiDIKs2qMTnL%2Bxgy8SOyrdAhReJ%2FKZ0SxGRasHYJRYsVxMJMhA25ChA6GqduwZIBlqtK9IxJnDE8aeV83jgQxvjY7KwMDAj%2FiCg8oToGUMbZasQOb2H%2BmqMIvcAf%2BMtR3aCfe17oyqKpwPhQLFrMjzLMJg94T4Qr1vS%2FCZMSy%2F%2FhOAZn%2FqdAKSCuAWTDDuGp%2FGUHKlitTYxN8Sl056LZmQ07U%2BMKWAcvPz16CDMNsPp%2FK7aJlQciQNiFeRDq5I3Ue0QMBb0%2FBUFVDAzW%2FSV8TuzGYHI7WkfN1S1ozWnKVqZ%2BhOn%2BUBxgg86LlfkugZDA%2B1FZ0%2BH31m%2BFPj%2BlZYM1OTVzdVYN1vM8vjkEnSaGJoFPrJJYeIWW%2BKLnphFNQGAtk7MqUDONCq54YxI4%2BQ%2BpZgox3%2BBh7tiu7QVoGL3%2FX9Tt7EPJ2F9t0xVnEEO7GKfrFoLbHMrnhzlwNAlq%2FItl3jsHD34LIsKAqobBucwE4wkcnXzAY6ngESAZj4wIbxNUrHWzRkqyPMKXAsvXZtBP54rNLiF%2BsP34wFseddwmXVVCBVF44H5mXYqtErADaWoIUXcr6myZDd4jiXiaZr9UqA%2Fb3ZkqGIWD%2BvFtwrtuJ%2BzmZ9Z%2FIHPXgRmT7vkqaY665k6esgbPn8xgrZa5zkT%2BlkEHuHFGUjjRGZlcEI5TvYMBxb2sTrdnZwgEMbFcDg6iOzfcMd%2Bg%3D%3D&Expires=1771434658",
  "expiresInSeconds": 3600
}
Opened image in default browser for photoId=6acff99e456140bfbb3756639a4f6e27.
Requesting download URL for selected photoId=6e6051b2f8d84598acee5b9d4d479728...
GET /photos/{photoId}/download-url -> 200
{
  "downloadUrl": "https://millerpic-photos-dev.s3.amazonaws.com/originals/110732209307403665878/6e6051b2f8d84598acee5b9d4d479728.webp?AWSAccessKeyId=ASIA5PLWJANYF3EEN2J5&Signature=ac8HlYpRxpN%2FlEPvlfkdByg6ED0%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEKH%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIBStZvg%2FutjAo4Q7Y%2BL2%2Fp55Vm7zU8I5EAySQ4eoavi3AiEA1luZVxGFh0LC6KdjIl2uDxO%2BM5MQwW8m654SkB5zjYoqgAMIaRAEGgw5MjYzNTAzNzc4NDAiDIKs2qMTnL%2Bxgy8SOyrdAhReJ%2FKZ0SxGRasHYJRYsVxMJMhA25ChA6GqduwZIBlqtK9IxJnDE8aeV83jgQxvjY7KwMDAj%2FiCg8oToGUMbZasQOb2H%2BmqMIvcAf%2BMtR3aCfe17oyqKpwPhQLFrMjzLMJg94T4Qr1vS%2FCZMSy%2F%2FhOAZn%2FqdAKSCuAWTDDuGp%2FGUHKlitTYxN8Sl056LZmQ07U%2BMKWAcvPz16CDMNsPp%2FK7aJlQciQNiFeRDq5I3Ue0QMBb0%2FBUFVDAzW%2FSV8TuzGYHI7WkfN1S1ozWnKVqZ%2BhOn%2BUBxgg86LlfkugZDA%2B1FZ0%2BH31m%2BFPj%2BlZYM1OTVzdVYN1vM8vjkEnSaGJoFPrJJYeIWW%2BKLnphFNQGAtk7MqUDONCq54YxI4%2BQ%2BpZgox3%2BBh7tiu7QVoGL3%2FX9Tt7EPJ2F9t0xVnEEO7GKfrFoLbHMrnhzlwNAlq%2FItl3jsHD34LIsKAqobBucwE4wkcnXzAY6ngESAZj4wIbxNUrHWzRkqyPMKXAsvXZtBP54rNLiF%2BsP34wFseddwmXVVCBVF44H5mXYqtErADaWoIUXcr6myZDd4jiXiaZr9UqA%2Fb3ZkqGIWD%2BvFtwrtuJ%2BzmZ9Z%2FIHPXgRmT7vkqaY665k6esgbPn8xgrZa5zkT%2BlkEHuHFGUjjRGZlcEI5TvYMBxb2sTrdnZwgEMbFcDg6iOzfcMd%2Bg%3D%3D&Expires=1771434669",
  "expiresInSeconds": 3600
}
Opened image in default browser for photoId=6e6051b2f8d84598acee5b9d4d479728.

- [ ] 8) Search/filter behavior works as expected (if present)
I was able to search for and open "0220723_121102.jpg"
I also did the upload again of Web capture_7-11-2021_18379_myaccount.gflenv.com.jpeg, and was able to subsequently search and open the file. I think I messed up the upload the first time. Maybe I didn't click the button. 
- [ ] 9) Metadata update path works (if present)
not sure I see this or know how to do it
- [ ] 10) Delete/trash flow works and item leaves main list
don't see an option for deleting a file
- [ ] 11) Hard-delete flow works (if exposed)
con't see an option to delete a file
- [ ] 12) Network interruption handled gracefully (clear error/retry)
disconnected and reconnected wifi with no problems
- [ ] 13) Session persistence behaves as expected after restart
after restarting the app I have to redo the sign in , there is no persistence
- [ ] 14) Sign-out works and protected actions require re-auth
signout works

## Step-by-Step Results
Use one line per step.

| Step | PASS/FAIL | Time | Notes | Error Message (exact) | Screenshot |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |
| 4 |  |  |  |  |  |
| 5 |  |  |  |  |  |
| 6 |  |  |  |  |  |
| 7 |  |  |  |  |  |
| 8 |  |  |  |  |  |
| 9 |  |  |  |  |  |
| 10 |  |  |  |  |  |
| 11 |  |  |  |  |  |
| 12 |  |  |  |  |  |
| 13 |  |  |  |  |  |
| 14 |  |  |  |  |  |

## Failure Details (if any)
- Failure 1:
  - Repro steps:
  - Expected:
  - Actual:
  - Retry worked (yes/no):
- Failure 2:
  - Repro steps:
  - Expected:
  - Actual:
  - Retry worked (yes/no):

## Final Assessment
- Overall status: `needs-fix`
- Blockers: Desktop window does not fit 1080p and there is no app-level scrolling to reach all controls; list/pagination behavior is unclear and appears inconsistent after changing limit values.
- Nice-to-have fixes: Improve overall visual polish and usability flow of the desktop UI after core fit/function issues are fixed.
- Anything unexpected: Upload/search works when repeated carefully, but initial upload/list validation was confusing and looked inconsistent during the same session.

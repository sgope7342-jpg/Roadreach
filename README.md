# RoadReach — Jamshedpur pilot

## Exact flow
1. Vehicle owner opens **Register vehicle** and enters their name, mobile number and vehicle details.
2. After submission, the app creates a unique serial number (for example `RR-JSR-0001`) and a QR code.
3. Owner downloads/prints the QR and serial number together and places the sticker on the vehicle.
4. Anyone scanning the QR is taken to the RoadReach **Contact Owner** page.
5. They type the serial number printed on the sticker. If it matches a registered vehicle, the owner phone number and call button appear.

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## Important before public launch
- This is a working prototype, not a deployed public website.
- Phone ownership is not OTP-verified yet. Use test data until verification and consent protections are added.
- Anyone who knows a valid serial number can see the registered phone number.
- Configure a strong `SECRET_KEY`, HTTPS, persistent database/backups, rate limiting and abuse reporting before launch.
- The roadside-help and SOS request forms only record requests; they do not dispatch help or notify emergency services. For immediate emergencies in India, call 112.

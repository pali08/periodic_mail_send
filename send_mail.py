import argparse
import getpass
import time

import cv2

"""Send the contents of a directory as a MIME message."""

# For guessing MIME type based on file name extension
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import signal
import sys
import time


def get_writer(videoformat, codec, fps, camera=0):
    cap = cv2.VideoCapture(camera)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter('videoattachment.{}'.format(videoformat), cv2.VideoWriter_fourcc(*codec), fps, (width, height))
    return cap, writer


def record_video(cap, writer, time_recording):
    start_time = time.time()
    while time.time() - start_time < time_recording:
        ret, frame = cap.read()
        writer.write(frame)
        cv2.imshow('frame', frame)
    cap.release()
    writer.release()
    cv2.destroyAllWindows()


def setup_mime(sender_address, receiver_address, subject, mail_content):
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = subject
    # The subject line
    # The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))
    return message


def handle_file(filepath, message):
    with open(filepath, 'rb') as attach_file:  # Open the file as binary mode
        payload = MIMEBase('application', 'octate-stream')
        payload.set_payload((attach_file).read())
        encoders.encode_base64(payload)  # encode the attachment
        # add payload header with filename
        payload.add_header('Content-Decomposition', 'attachment', filename=filepath)
        message.attach(payload)
    return message


def send_mail_in_session(smtp_server, sender_address, receiver_address, sender_pass, message):
    # Create SMTP session for sending the mail
    session = smtplib.SMTP(smtp_server, 587)  # use gmail with port
    session.starttls()  # enable security
    session.login(sender_address, sender_pass)  # login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')


def record_and_send(sender_address, recip_address, subject, mail_content,
                    smtp_server, sender_pass, video_lenght, time_before_next_video, num_of_cycles, file_format='mp4',
                    codec='DIVX',
                    fps=20,
                    camera=0):
    for i in range(0, num_of_cycles):
        cap, writer = get_writer(file_format, codec, fps, camera)
        time_before_video_recording = time.time()
        record_video(cap, writer, video_lenght)
        time_after_video_recording = time.time()
        print('Video was recorded {}'.format(time_after_video_recording - time_before_video_recording))
        message_for_send = setup_mime(sender_address, recip_address, subject, mail_content)
        message_for_send = handle_file('videoattachment.{}'.format(file_format), message_for_send)
        send_mail_in_session(smtp_server, sender_address, recip_address, sender_pass, message_for_send)
        time_before_sleep = time.time()
        time.sleep(time_before_next_video)
        time_after_sleep = time.time()
        print('Sleeping between video recording laster {}.'.format(time_after_sleep - time_before_sleep))


if __name__ == '__main__':
    sender_pass_ = getpass.getpass(prompt='insert you password:')
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('sender_address',
                        help='Sender`s address', type=str)
    parser.add_argument('recip_address',
                        help='Recipient`s address', type=str)
    parser.add_argument('subject',
                        help='Subject of mail', type=str)
    parser.add_argument('mail_content',
                        help='Some short message - body of an e-mail', type=str)
    parser.add_argument('smtp_server',
                        help='SMTP server', type=str)
    parser.add_argument('video_length',
                        help='How long videos do we want to record ?', type=int)
    parser.add_argument('interval_between_two_recordings',
                        help='How often do we want to record ?', type=int)
    parser.add_argument('count_of_cycles',
                        help='How many cycles of record->sleep do you want ?', type=int)
    parser.add_argument('--video_format', '-v', nargs='?', const='mp4', default='mp4',
                        help='Video format (matches with 3 letter suffix usually)',
                        type=str)
    parser.add_argument('--codec', '-c', nargs='?', const='DIVX', default='DIVX', help='Video codec',
                        type=str)
    parser.add_argument('--fps', '-f', nargs='?', const=20, default=20, help='Frame per second',
                        type=int)
    parser.add_argument('--camera', '-a', nargs='?', const=0, default=0,
                        help='The camera used. Default camera is zero.',
                        type=int)

    args = parser.parse_args()
    record_and_send(args.sender_address, args.recip_address, args.subject, args.mail_content,
                    args.smtp_server, sender_pass_, args.video_length, args.interval_between_two_recordings,
                    args.count_of_cycles,
                    args.video_format, args.codec,
                    args.fps,
                    args.camera)

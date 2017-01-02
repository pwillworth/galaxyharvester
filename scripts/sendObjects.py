#!/usr/bin/env python

from uuid import uuid4 as uuid
import sys

from dreamObjects import DreamObjects

sendobjects = [['ioscode_public','ghWebFiles.tgz']]

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='DreamObject App')

    parser.add_argument(
        '--access-key',
        action='store',
        dest='access_key',
        help='DreamObjects S3 Access Key',
        required=True
    )
    parser.add_argument(
        '--secret-key',
        action='store',
        dest='secret_key',
        help='DreamObjects S3 Secret Key',
        required=True
    )
    parser.add_argument(
        '--use-s3',
        action='store_true',
        dest='use_s3',
        default=False,
        help='Use S3 rather than DreamObjects'
    )

    args = parser.parse_args()

    for sendobj in sendobjects:
        do = DreamObjects(
            access_key=args.access_key,
            secret_key=args.secret_key,
            bucket_name=sendobj[0],
            object_name=sendobj[1],
            use_s3=args.use_s3,
            show_http_traffic=True
        )

	do.create_connection()
	do.create_bucket()
	do.store_object()
	do.get_public_reference()
	do.key.set_canned_acl('public-read')
	print do.public_url

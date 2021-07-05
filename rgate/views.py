import urllib.request
import numpy as np
import random
import redis
import string
import time
from django.http import JsonResponse
from django.conf import settings

cache = redis.Redis(host='127.0.0.1', port=6379)


def default_view(request):
    """
    Default view that decides what to show to the user
    And also manages latency
    """
    url = request.get_full_path()
    print('URL:', url)
    if url == '/stats':
        latency = []
        for key in cache.scan_iter('hit:*'):
            latency.append(cache.get(key))
        print(latency)
        return JsonResponse({
            'request_count' : {
                'success': int(cache.get('success')) if cache.get('success') else 0,
                'error': int(cache.get('error')) if cache.get('error') else 0
            },
            'latency_ms': {
                'average': round(np.average(latency)) if latency else 0,
                'p95': round(np.percentile(latency, 95)) if latency else 0,
                'p99': round(np.percentile(latency, 99)) if latency else 0
            }
        })
    else:
        # current url is not in backends: throw error
        url = 'http://127.0.0.1:9001' + url
        if url not in settings.BACKENDS.values():
            cache.incr('error')
            return JsonResponse({'message': settings.DEFAULT_ERROR_MESSAGE}, status=settings.DEFAULT_ERROR_CODE)
        
        try:
            start_time = time.time()
            conn = urllib.request.urlopen(url)
            cache.incr('success')
            # Generates random string with all caps of size 5
            latency_key = str(time.time()) + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            latency = int((time.time()-start_time) * 1000) # Saving in milli seconds
            cache.set(latency_key, round(latency))
            print('Latency inserted', latency_key, '%s microseconds' % latency)
            return JsonResponse({'message': 'Success'})
        except urllib.error.HTTPError as e:
            # It handles all the error code
            if e.code > 399:
                cache.incr('error')
                if e.code > 500:
                    return JsonResponse({'message': 'Server is not available'}, status=503)
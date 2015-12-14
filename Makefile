all:
	make -C cprog

clean:
	make -C cprog clean
	rm *.pyc 2>/dev/null

video:
	avconv -framerate 5 -f image2 -i "/tmp/out/%d0.png" -b 65536k -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" run.mov
	#avconv -framerate 3 -f image2 -i "/tmp/record/%d0.jpg" -b 65536k -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" run.mov

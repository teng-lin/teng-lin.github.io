---
layout: post
title: Docker Source Code Reading Series - Part 1
---
[Docker](http://www.docker.com/) is the most promising technology for software development and deployment in the last decade.

This is the first post of a seriers of blog posts that records my personal experience in diving into the docker source code. Hopefully, it will also help developers who are new to docker to have better understanding of the internals of the [docker source code](https://github.com/docker/docker/tree/release-1.3).

## Basic concept
It is very important to familiar yourself with a few basic concepts.

1. [Layer](https://docs.docker.com/terms/layer)
2. [Image](https://docs.docker.com/terms/image/)
3. [Container](https://docs.docker.com/terms/container/)

## Docker Binary

Below code snippet extracted from [docker.go](https://github.com/docker/docker/blob/release-1.3/docker/docker.go) is the main entry point of docker.

{% highlight go linenos %}

func main() {
	if reexec.Init() {
		return
	}

	flag.Parse()
	// FIXME: validate daemon flags here

	if *flVersion {
		showVersion()
		return
	}

	if *flLogLevel != "" {
		lvl, err := log.ParseLevel(*flLogLevel)
		if err != nil {
			log.Fatalf("Unable to parse logging level: %s", *flLogLevel)
		}
		initLogging(lvl)
	} else {
		initLogging(log.InfoLevel)
	}

	// -D, --debug, -l/--log-level=debug processing
	// When/if -D is removed this block can be deleted
	if *flDebug {
		os.Setenv("DEBUG", "1")
		initLogging(log.DebugLevel)
	}

	if len(flHosts) == 0 {
		defaultHost := os.Getenv("DOCKER_HOST")
		if defaultHost == "" || *flDaemon {
			// If we do not have a host, default to unix socket
			defaultHost = fmt.Sprintf("unix://%s", api.DEFAULTUNIXSOCKET)
		}
		defaultHost, err := api.ValidateHost(defaultHost)
		if err != nil {
			log.Fatal(err)
		}
		flHosts = append(flHosts, defaultHost)
	}

	if *flDaemon {
		mainDaemon()
		return
	}

	if len(flHosts) > 1 {
		log.Fatal("Please specify only one -H")
	}
	protoAddrParts := strings.SplitN(flHosts[0], "://", 2)

	var (
		cli       *client.DockerCli
		tlsConfig tls.Config
	)
	tlsConfig.InsecureSkipVerify = true

	// Regardless of whether the user sets it to true or false, if they
	// specify --tlsverify at all then we need to turn on tls
	if flag.IsSet("-tlsverify") {
		*flTls = true
	}

	// If we should verify the server, we need to load a trusted ca
	if *flTlsVerify {
		certPool := x509.NewCertPool()
		file, err := ioutil.ReadFile(*flCa)
		if err != nil {
			log.Fatalf("Couldn't read ca cert %s: %s", *flCa, err)
		}
		certPool.AppendCertsFromPEM(file)
		tlsConfig.RootCAs = certPool
		tlsConfig.InsecureSkipVerify = false
	}

	// If tls is enabled, try to load and send client certificates
	if *flTls || *flTlsVerify {
		_, errCert := os.Stat(*flCert)
		_, errKey := os.Stat(*flKey)
		if errCert == nil && errKey == nil {
			*flTls = true
			cert, err := tls.LoadX509KeyPair(*flCert, *flKey)
			if err != nil {
				log.Fatalf("Couldn't load X509 key pair: %s. Key encrypted?", err)
			}
			tlsConfig.Certificates = []tls.Certificate{cert}
		}
		// Avoid fallback to SSL protocols < TLS1.0
		tlsConfig.MinVersion = tls.VersionTLS10
	}

	if *flTls || *flTlsVerify {
		cli = client.NewDockerCli(os.Stdin, os.Stdout, os.Stderr, nil, protoAddrParts[0], protoAddrParts[1], &tlsConfig)
	} else {
		cli = client.NewDockerCli(os.Stdin, os.Stdout, os.Stderr, nil, protoAddrParts[0], protoAddrParts[1], nil)
	}

	if err := cli.Cmd(flag.Args()...); err != nil {
		if sterr, ok := err.(*utils.StatusError); ok {
			if sterr.Status != "" {
				log.Println(sterr.Status)
			}
			os.Exit(sterr.StatusCode)
		}
		log.Fatal(err)
	}
}

{% endhighlight %}


Docker binary is a stunt double, which contains both daemon (see line 45) and client (see line 100).
 
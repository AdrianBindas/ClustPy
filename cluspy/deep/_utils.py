import torch


class Simple_Autoencoder(torch.nn.Module):
    """A vanilla symmetric autoencoder.

    Args:
        input_dim: size of each input sample
        embedding_size: size of the inner most layer also called embedding

    Attributes:
        encoder: encoder part of the autoencoder, responsible for embedding data points
        decoder: decoder part of the autoencoder, responsible for reconstructing data points from the embedding
    """

    def __init__(self, input_dim: int, embedding_size: int, small_network=False):
        super(Simple_Autoencoder, self).__init__()

        if small_network:
            # make a sequential list of all operations you want to apply for encoding a data point
            self.encoder = torch.nn.Sequential(
                # Linear layer (just a matrix multiplication)
                torch.nn.Linear(input_dim, 256),
                # apply an elementwise non-linear function
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(256, 128),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(128, 64),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(64, embedding_size))

            # make a sequential list of all operations you want to apply for decoding a data point
            # In our case this is a symmetric version of the encoder
            self.decoder = torch.nn.Sequential(
                torch.nn.Linear(embedding_size, 64),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(64, 128),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(128, 256),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(256, input_dim),
            )
        else:
            # make a sequential list of all operations you want to apply for encoding a data point
            self.encoder = torch.nn.Sequential(
                # Linear layer (just a matrix multiplication)
                torch.nn.Linear(input_dim, 500),
                # apply an elementwise non-linear function
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(500, 500),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(500, 2000),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(2000, embedding_size))

            # make a sequential list of all operations you want to apply for decoding a data point
            # In our case this is a symmetric version of the encoder
            self.decoder = torch.nn.Sequential(
                torch.nn.Linear(embedding_size, 2000),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(2000, 500),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(500, 500),
                torch.nn.LeakyReLU(inplace=True),
                torch.nn.Linear(500, input_dim),
            )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: input data point, can also be a mini-batch of points

        Returns:
            embedded: the embedded data point with dimensionality embedding_size
        """
        return self.encoder(x)

    def decode(self, embedded: torch.Tensor) -> torch.Tensor:
        """
        Args:
            embedded: embedded data point, can also be a mini-batch of embedded points

        Returns:
            reconstruction: returns the reconstruction of a data point
        """
        return self.decoder(embedded)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """ Applies both encode and decode function.
        The forward function is automatically called if we call self(x).
        Args:
            x: input data point, can also be a mini-batch of embedded points

        Returns:
            reconstruction: returns the reconstruction of a data point
        """
        embedded = self.encode(x)
        reconstruction = self.decode(embedded)
        return reconstruction

    def start_training(self, trainloader, n_epochs, device, optimizer, loss_fn):
        for _ in range(n_epochs):
            for batch in trainloader:
                # load batch on device
                batch_data = batch.to(device)
                reconstruction = self.forward(batch_data)
                loss = loss_fn(reconstruction, batch_data)
                # reset gradients from last iteration
                optimizer.zero_grad()
                # calculate gradients and reset the computation graph
                loss.backward()
                # update the internal params (weights, etc.)
                optimizer.step()


def squared_euclidean_distance(centers, embedded, weights=None):
    ta = centers.unsqueeze(0)
    tb = embedded.unsqueeze(1)
    squared_diffs = (ta - tb)
    if weights is not None:
        weights_unsqueezed = weights.unsqueeze(0).unsqueeze(1)
        squared_diffs = squared_diffs * weights_unsqueezed
    squared_diffs = squared_diffs.pow(2).sum(2)  # .mean(2) # TODO Evaluate this change
    return squared_diffs


def detect_device():
    """Automatically detects if you have a cuda enabled GPU"""
    if torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    return device


def encode_batchwise(dataloader, model, device):
    """ Utility function for embedding the whole data set in a mini-batch fashion
    """
    embeddings = []
    for batch in dataloader:
        batch_data = batch.to(device)
        embeddings.append(model.encode(batch_data).detach().cpu())
    return torch.cat(embeddings, dim=0).numpy()


def predict_batchwise(dataloader, model, cluster_module, device):
    """ Utility function for predicting the cluster labels over the whole data set in a mini-batch fashion
    """
    predictions = []
    for batch in dataloader:
        batch_data = batch.to(device)
        prediction = cluster_module.prediction_hard(model.encode(batch_data)).detach().cpu()
        predictions.append(prediction)
    return torch.cat(predictions, dim=0).numpy()


def get_trained_autoencoder(trainloader, learning_rate, n_epochs, device, optimizer_class, loss_fn,
                            input_dim, embedding_size, autoencoder_class=Simple_Autoencoder):
    if embedding_size > input_dim:
        print(
            "WARNING: embedding_size is larger than the dimensionality of the input dataset. Setting embedding_size to",
            input_dim)
        embedding_size = input_dim
    # Pretrain Autoencoder
    # adjusted here
    if autoencoder_class is Simple_Autoencoder:
        autoencoder = autoencoder_class(input_dim=input_dim, embedding_size=embedding_size).to(device)
        optimizer = optimizer_class(autoencoder.parameters(), lr=learning_rate)
        autoencoder.start_training(trainloader, n_epochs, device, optimizer, loss_fn)
    else: ### added this
        #n_features = data.shape[1]
        ### die eventuell mal als Parameter
        ae_layout = [500, 500, 2000, embedding_size]
        steps_per_layer = 25000
        refine_training_steps = 50000
        ###
        autoencoder = autoencoder_class(input_dim, ae_layout, weight_initalizer=torch.nn.init.xavier_normal_,
        activation_fn=lambda x: F.relu(x), loss_fn=loss_fn, optimizer_fn=lambda parameters: torch.optim.Adam(parameters, lr=learning_rate))
        # train and testloader
        #trainloader, testloader = get_train_and_testloader(data, gt_labels, batch_size)
        autoencoder.pretrain(trainloader, rounds_per_layer=steps_per_layer, dropout_rate=0.2, corruption_fn=add_noise)
        autoencoder.refine_training(trainloader, refine_training_steps, corruption_fn=add_noise)
        #total_loss = get_total_loss(autoencoder,trainloader) <--- Hat mir einen Fehler geschmissen
        #print(total_loss)
    return autoencoder


def int_to_one_hot(label_tensor, n_labels):
    onehot = torch.zeros([label_tensor.shape[0], n_labels], dtype=torch.float, device=label_tensor.device)
    onehot.scatter_(1, label_tensor.unsqueeze(1).long(), 1.0)
    return onehot

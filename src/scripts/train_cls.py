import os
import sys
import torch
import numpy as np
import importlib
import shutil
import argparse
from pathlib import Path
from tqdm import tqdm

from torch.utils.data import DataLoader
from data_utils.ModelNetDataLoader import ModelNetDataLoader
from point_net_suite.models.point_net_cls import PointNetClassification
import data_utils.DataAugmentationAndShuffle as DataAugmentator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
models_folder_dict = {'pointnet_cls': 'models/Pointnet'}
models_modules_dict = {'pointnet_cls': 'pointnet_classification'}

def parse_args():
    '''PARAMETERS'''
    parser = argparse.ArgumentParser('training')
    parser.add_argument('--use_cpu', action='store_true', default=False, help='use cpu mode')
    #parser.add_argument('--gpu', type=str, default='0', help='specify gpu device')
    parser.add_argument('--batch_size', type=int, default=24, help='batch size in training')
    parser.add_argument('--model', default='pointnet_cls', help='model name [default: pointnet_cls]')
    parser.add_argument('--num_category', default=40, type=int, choices=[10, 40],  help='training on ModelNet10/40')
    parser.add_argument('--epoch', default=20, type=int, help='number of epoch in training')
    parser.add_argument('--learning_rate', default=0.001, type=float, help='learning rate in training')
    parser.add_argument('--num_point', type=int, default=1024, help='Point Number')
    parser.add_argument('--dropout', type=float, default=0.4, help='Dropout')
    parser.add_argument('--optimizer', type=str, default='AdamW', help='optimizer for training')
    #parser.add_argument('--log_dir', type=str, default=None, help='experiment root')
    parser.add_argument('--decay_rate', type=float, default=1e-4, help='decay rate')
    parser.add_argument('--use_normals', action='store_true', default=False, help='use normals')
    parser.add_argument('--process_data', action='store_true', default=False, help='save data offline')
    parser.add_argument('--use_uniform_sample', action='store_true', default=False, help='use uniform sampiling')
    parser.add_argument('--remove_checkpoint', action='store_true', default=False, help='remove last checkpoint train progress')
    return parser.parse_args()


def test(model, loader, num_class=40):
    # Matrix to store the per class accuracy
    class_acc = np.zeros((num_class, 3)) #dim0 = accumulated sum of accuracies, dim1 = number of batches, dim2 = accuracy per class calculated in the end of the loop (dim0 / dim1)
    # Array to store the batch accuracy (ratio of total correct predictions per batch)
    mean_correct = []
    
    classifier = model.eval()

    for j, (points, target) in tqdm(enumerate(loader), total=len(loader)):

        if not args.use_cpu:
            points, target = points.cuda(), target.cuda()

        points = points.transpose(2, 1)
        pred, crit_idxs, feat_trans = classifier(points)
        # Chooses the class with the highest probability for each point in the batch (pred is a matrix of shape = (num_points in bactch, num_clases) where the second dimension is the probability predicted for each class)
        pred_choice = pred.data.max(1)[1]

        # Class accuracy calculation
        for curr_class in np.unique(target.cpu()):
            # Compares the predictions masked with the current class, effectively counting the number of correct predictions for the current class with sum
            curr_cat_classacc = pred_choice[target == curr_class].eq(target[target == curr_class].long().data).cpu().sum()
            # Computes and accumulates the accuracy for the class in the current batch (number of correct predictions divided by the number of samples for the class)
            class_acc[curr_class, 0] += curr_cat_classacc.item() / float(points[target == curr_class].size()[0])
            # Adds one more batch count to the class (so we can later get the mean class accuracy - we will have the accumulation of accuracy and the number of batches to divide the accumulation by)
            class_acc[curr_class, 1] += 1 

        # Batch accuracy calculation
        correct = pred_choice.eq(target.long().data).cpu().sum()
        mean_correct.append(correct.item() / float(points.size()[0]))

    # Get the accuracy per class by dividing the accumulated accuracy by the batch count and store it in dim2
    class_acc[:, 2] = class_acc[:, 0] / class_acc[:, 1]
    # Get the mean accuracy for all classes
    mean_class_acc = np.mean(class_acc[:, 2])

    # Calculate the mean of the batches accuracy
    instance_acc = np.mean(mean_correct)

    return instance_acc, mean_class_acc


def main(args):
    def log_string(str):
        #logger.info(str)
        print(str)

    #'''HYPER PARAMETER'''
    #os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

    '''CREATE DIR'''
    exp_dir = Path('./log/')
    exp_dir.mkdir(exist_ok=True)
    exp_dir = exp_dir.joinpath('classification')
    exp_dir.mkdir(exist_ok=True)
    #if args.log_dir is None:
    #    timestr = str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M'))
    #    exp_dir = exp_dir.joinpath(timestr)
    #else:
    exp_dir = exp_dir.joinpath(args.model)
    if args.remove_checkpoint and exp_dir.exists():
        log_string('Deleting existing checkpoint!')
        shutil.rmtree(exp_dir)
    exp_dir.mkdir(exist_ok=True)
    #checkpoints_dir = exp_dir.joinpath('checkpoints/')
    #checkpoints_dir.mkdir(exist_ok=True)

    #'''LOG'''
    #log_dir = exp_dir.joinpath('logs/')
    #log_dir.mkdir(exist_ok=True)
    #args = parse_args()
    #logger = logging.getLogger("Model")
    #logger.setLevel(logging.INFO)
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #file_handler = logging.FileHandler('%s/%s.txt' % (log_dir, args.model))
    #file_handler.setLevel(logging.INFO)
    #file_handler.setFormatter(formatter)
    #logger.addHandler(file_handler)
    log_string('PARAMETER ...')
    log_string(args)

    '''DATA LOADING'''
    log_string('Load dataset ...')
    data_path = 'data/modelnet40/'

    train_dataset = ModelNetDataLoader(root=data_path, args=args, split='train', process_data=args.process_data)
    test_dataset = ModelNetDataLoader(root=data_path, args=args, split='test', process_data=args.process_data)
    trainDataLoader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=8, drop_last=True)
    testDataLoader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=8)

    '''MODEL LOADING'''
    sys.path.append(os.path.join(BASE_DIR, models_folder_dict[args.model]))
    num_class = args.num_category
    model = PointNetClassification(models_modules_dict[args.model])
    #shutil.copy('./models/%s.py' % args.model, str(exp_dir))
    #shutil.copy('models/pointnet2_utils.py', str(exp_dir))
    #shutil.copy('./train_classification.py', str(exp_dir))

    classifier = model.get_model(num_points=args.num_point, k=num_class, dropout=args.dropout)
    criterion = model.get_loss()
    #classifier.apply(inplace_relu)

    if not args.use_cpu:
        classifier = classifier.cuda()
        criterion = criterion.cuda()

    if args.optimizer == 'Adam':
        optimizer = torch.optim.Adam(
            classifier.parameters(),
            lr=args.learning_rate,
            betas=(0.9, 0.999),
            eps=1e-08,
            weight_decay=args.decay_rate
        )
    elif args.optimizer == 'AdamW':
        optimizer = torch.optim.AdamW(
            classifier.parameters(),
            lr=args.learning_rate,
            betas=(0.9, 0.999),
            eps=1e-08,
            weight_decay=args.decay_rate
        )
    else:
        optimizer = torch.optim.SGD(classifier.parameters(), lr=args.learning_rate, momentum=0.9)

    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.7)

    try:
        checkpoint = torch.load(str(exp_dir) + '/best_model.pth')
        start_epoch = checkpoint['epoch']
        classifier.load_state_dict(checkpoint['model_state_dict'])
        log_string('Use pretrain model')
    except:
        log_string('No existing model, starting training from scratch...')
        start_epoch = 0
    
    global_epoch = 0
    global_step = 0
    best_instance_acc = 0.0
    best_class_acc = 0.0

    train_accuracy = []
    test_accuracy = []
    test_mean_class_accuracy = []

    '''TRANING'''
    log_string('Start training...')
    for epoch in range(start_epoch, args.epoch):
        log_string('Epoch %d (%d/%s):' % (global_epoch + 1, epoch + 1, args.epoch))
        mean_correct = []
        classifier = classifier.train()

        scheduler.step()
        for batch_id, (points, target) in tqdm(enumerate(trainDataLoader, 0), total=len(trainDataLoader), smoothing=0.9):
            optimizer.zero_grad()

            points = points.data.numpy()
            points = DataAugmentator.random_point_dropout(points)
            points[:, :, 0:3] = DataAugmentator.random_scale_point_cloud(points[:, :, 0:3])
            points[:, :, 0:3] = DataAugmentator.shift_point_cloud(points[:, :, 0:3])
            points = torch.Tensor(points)
            points = points.transpose(2, 1)

            if not args.use_cpu:
                points, target = points.cuda(), target.cuda()

            pred, crit_idxs, feat_trans = classifier(points)

            loss = criterion(pred, target.long(), feat_trans)
            pred_choice = pred.data.max(1)[1]

            correct = pred_choice.eq(target.long().data).cpu().sum()
            mean_correct.append(correct.item() / float(points.size()[0]))
            loss.backward()
            optimizer.step()
            global_step += 1

        train_instance_acc = np.mean(mean_correct)
        train_accuracy.append(train_instance_acc)
        log_string('Train Instance Accuracy: %f' % train_instance_acc)

        with torch.no_grad():
            instance_acc, mean_class_acc = test(classifier.eval(), testDataLoader, num_class=num_class)

            test_accuracy.append(instance_acc)
            test_mean_class_accuracy.append(mean_class_acc)

            if (instance_acc >= best_instance_acc):
                best_instance_acc = instance_acc
                best_epoch = epoch + 1

            if (mean_class_acc >= best_class_acc):
                best_class_acc = mean_class_acc
            log_string('Test Instance Accuracy: %f, Mean Class Accuracy: %f' % (instance_acc, mean_class_acc))
            log_string('Best Instance Accuracy: %f, Mean Class Accuracy: %f' % (best_instance_acc, best_class_acc))

            if (instance_acc >= best_instance_acc):
                savepath = str(exp_dir) + '/best_model.pth'
                log_string('Saving model at %s' % savepath)
                state = {
                    'epoch': best_epoch,
                    'instance_acc': instance_acc,
                    'class_acc': mean_class_acc,
                    'model_state_dict': classifier.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                }
                torch.save(state, savepath)
            global_epoch += 1

    log_string('End of training...')


if __name__ == '__main__':
    args = parse_args()
    main(args)
